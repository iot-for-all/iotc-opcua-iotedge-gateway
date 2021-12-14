import json
import time
import os
import os.path
import sys
sys.path.insert(0, "..")
import base64
import hmac
import hashlib
import asyncio

# from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, X509

# device settings - FILL IN YOUR VALUES HERE
provisioning_host = "global.azure-devices-provisioning.net"
scope_id = os.environ['dpsScopeId']
group_symmetric_key = os.environ['dpsEnrollmentGroupSaskey']
model_id = os.environ['modelId']

await_timeout = 4.0
use_websockets = True
max_connection_attempt = 3

deviceClients = {}

# derives a symmetric device key for a device id using the group symmetric key
def derive_device_key(device_id, group_symmetric_key):
    message = device_id.encode("utf-8")
    signing_key = base64.b64decode(group_symmetric_key.encode("utf-8"))
    signed_hmac = hmac.HMAC(signing_key, message, hashlib.sha256)
    device_key_encoded = base64.b64encode(signed_hmac.digest())
    return device_key_encoded.decode("utf-8")

# connect using symmetric key
async def connectWithSaskey(registrationId, clientSecrets, customProperties):
    global deviceClients
    
    # print("connectWithSaskey: customProperties: {}".format(customProperties))
    gatewayId = customProperties.get('$.cdid')
    modelId = customProperties.get('modelId')
    if modelId == None:
        modelId = model_id
        
    client = deviceClients.get(registrationId)
    if client != None:
        print("connectWithSaskey: Fetched device client fron cached . . .")
        try:
            if client.connected:
                return client
            
            print("connectWithSaskey: Connecting the device client . . .")
            await client.connect()
            print("connectWithSaskey: Device client connected . . .")
            return client
        except Exception as ex:
            print("connectWithSaskey: Cached connection failed for device: {}, {}".format(registrationId, ex))
            deviceClients.pop(registrationId)
            
    device_client = None
    connected = False
    
    device_symmetric_key = derive_device_key(registrationId, group_symmetric_key)
    print("connectWithSaskey: Device saskey generated from masterKey: %s" % device_symmetric_key)
    
    if clientSecrets != None:
        print("connectWithSaskey: Device Secret: {}".format(clientSecrets))
        sas = clientSecrets.get("sas")
        if sas != None:
            device_symmetric_key = sas["key"]
            print("connectWithSaskey: Device saskey passed in: %s" % device_symmetric_key)
        
    print("connectWithSaskey: Device Symmetric Key: %s" % device_symmetric_key)
    connection_attempt_count = 0
    while not connected and connection_attempt_count < max_connection_attempt:
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host = provisioning_host,
            registration_id = registrationId,
            id_scope = scope_id,
            symmetric_key = device_symmetric_key,
            websockets = use_websockets
        )

        provisioning_device_client.provisioning_payload = '{"iotcGateway":{"iotcGatewayId":"%s"},"iotcModelId":"%s"}' % (gatewayId, modelId)
        print("----- DPS Provisioning payload:" + provisioning_device_client.provisioning_payload)
        registration_result = None

        try:
            print("connectWithSaskey: Provisioning device: %s" % registrationId)
            registration_result = await provisioning_device_client.register()
            print("connectWithSaskey: Device provisioned: %s" % registrationId)
        except Exception as e:
            print("connectWithSaskey: DPS registration exception: {}".format(e))
            connection_attempt_count += 1

        dps_registered = True if registration_result and registration_result.status == "assigned" else False
        if dps_registered:
            print("connectWithSaskey: Device registered: %s" % registrationId)
            hostname = os.getenv("IOTEDGE_GATEWAYHOSTNAME")
            connStr = "HostName=%s;DeviceId=%s;SharedAccessKey=%s" % (registration_result.registration_state.assigned_hub, registration_result.registration_state.device_id, device_symmetric_key)
            
            print("connectWithSaskey: connStr: %s" % connStr)
            print("connectWithSaskey: Creating device client fron connectionString returned by DPS . . .")
            device_client = IoTHubDeviceClient.create_from_connection_string(connStr, websockets=use_websockets)
            try:
                print("connectWithSaskey: Connecting the device client . . .")
                await device_client.connect()
                print("connectWithSaskey: Device client connected . . .")
                deviceClients[registrationId] = device_client
                connected = True
                print("connectWithSaskey: connected to central")
            except Exception as e:
                print("connectWithSaskey: Exception: {}".format(e))
                print("connectWithSaskey: Connection failed, retry %d of %d" % (connection_attempt_count, max_connection_attempt))
                connection_attempt_count += 1

    return device_client

# connect using X509
async def connectWithCert(registrationId, clientSecrets, customProperties):
    global deviceClients
    
    # print("connectWithCert: customProperties: {}".format(customProperties))
    gatewayId = customProperties.get('$.cdid')
    modelId = customProperties.get('modelId')
    if modelId == None:
        modelId = model_id
        
    client = deviceClients.get(registrationId)
    if client != None:
        print("connectWithCert: Fetched device client fron cached . . .")
        try:
            if client.connected:
                return client
            
            print("connectWithCert: Connecting the device client . . .")
            await client.connect()
            print("connectWithCert: Device client connected . . .")
            return client
        except Exception as ex:
            print("connectWithCert: Cached connection failed for device: {}, {}".format(registrationId, ex))
            deviceClients.pop(registrationId)
            
    device_client = None
    connected = False
    if clientSecrets == None or clientSecrets.get("cert") == None:
        print("connectWithCert: Device secrets is not provided . . .")
        return device_client

    print("connectWithCert: Setup Device X509")
    cert_file = customProperties.get('cert')
    key_file = customProperties.get('certKey')
    
    # cert_file = "/etc/certs/client02_public.pem"
    # key_file = "/etc/certs/client02_private.pem"
    print("cert_file: %s" % cert_file)
    print("key_file: %s" % key_file)
    if cert_file == None or key_file == None or os.path.exists(cert_file) == False or os.path.exists(key_file) == False:
        print("%s exists: %s" % (cert_file, os.path.exists(cert_file)))
        print("%s exists: %s" % (key_file, os.path.exists(key_file)))
        return device_client
    
    x509 = X509(cert_file, key_file)
    connection_attempt_count = 0
    while not connected and connection_attempt_count < max_connection_attempt:
        provisioning_device_client = ProvisioningDeviceClient.create_from_x509_certificate(
            provisioning_host = provisioning_host,
            registration_id = registrationId,
            id_scope = scope_id,
            x509 = x509,
            websockets = use_websockets
        )

        provisioning_device_client.provisioning_payload = '{"iotcGateway":{"iotcGatewayId":"%s"},"iotcModelId":"%s"}' % (gatewayId, modelId)
        print("----- DPS Provisioning payload:" + provisioning_device_client.provisioning_payload)
        registration_result = None

        try:
            print("connectWithCert: Provisioning device: %s" % registrationId)
            registration_result = await provisioning_device_client.register()
            print("connectWithCert: Device provisioned: %s" % registrationId)
        except Exception as e:
            print("connectWithCert: DPS registration exception: {}".format(e))
            connection_attempt_count += 1

        dps_registered = True if registration_result and registration_result.status == "assigned" else False
        if dps_registered:
            print("connectWithCert: Device registered: %s" % registrationId)
            hostname = os.getenv("IOTEDGE_GATEWAYHOSTNAME")
            
            print("connectWithCert: Creating device client using X509 returned by DPS . . .")
            device_client = IoTHubDeviceClient.create_from_x509_certificate(
                x509 = x509,
                hostname =registration_result.registration_state.assigned_hub,
                device_id = registration_result.registration_state.device_id,
                product_info = modelId,
                websockets=use_websockets
            )

            try:
                print("connectWithCert: Connecting the device client . . .")
                await device_client.connect()
                print("connectWithCert: Device client connected . . .")
                deviceClients[registrationId] = device_client
                connected = True
                print("connectWithCert: connected to central")
            except Exception as e:
                print("connectWithCert: Exception: {}".format(e))
                print("connectWithCert: Connection failed, retry %d of %d" % (connection_attempt_count, max_connection_attempt))
                connection_attempt_count += 1

    return device_client

async def connect(registrationId, customProperties):
    # print("connect: customProperties: {}".format(customProperties))    
    secrets = customProperties.get('secrets')
    clientSecret = None
    if secrets != None:
        b64Decoded = base64.b64decode(secrets.encode('utf-8'))
        secretsString = b64Decoded.decode("utf-8")
        # secrets = eval(secretsString)
        secrets = json.loads(secretsString)
        print("connect: Device secrets passed in: {}".format(secrets))
        
        clientSecret = secrets.get("client")
        if clientSecret != None:
            # print("connect: clientSecrets {}".format(clientSecret))
            if clientSecret.get("type") == "cert":
                print("connect: Connecting '%s' using connectWithCert" % registrationId)
                return await connectWithCert(registrationId, clientSecret, customProperties)
            if clientSecret.get("type") == "sas":
                print("connect: Connecting '%s' using connectWithSasKey" % registrationId)
                return await connectWithSaskey(registrationId, clientSecret, customProperties)
    
    # default connect
    print("connect: Connecting '%s' defaulting to use connectWithSasKey" % registrationId)
    return await connectWithSaskey(registrationId, clientSecret, customProperties)

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )
        print ("env variables: %s, %s, %s" % (scope_id, group_symmetric_key, model_id))

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()
        
        # print("os.environ: {}".format(os.environ))
        # define behavior for receiving an input message on input1
        async def input1_listener(client):
            while True:
                try:
                    input_message = await client.receive_message_on_input("input1")
                    message = input_message.data
                    size = len(message)
                    message_text = message.decode('utf-8')
                    print ( "===>> Data: %s & Size=%d" % (message_text, size) )
                    custom_properties = input_message.custom_properties
                    # print ( "      Properties: %s" % custom_properties )
                    registrationId = custom_properties.get('registrationId')
                    if registrationId != None:
                        print ( "      registrationId: %s" % registrationId )
                        deviceClient = await connect(registrationId, custom_properties)
                        if deviceClient and deviceClient.connected:
                            msg = Message(input_message.data)
                            msg.content_type = "application/json"
                            msg.content_encoding = "utf-8"
                            try:
                                await deviceClient.send_message(msg)
                                print("<<< completed sending message to iothub")
                            except asyncio.TimeoutError:
                                print("call to send message to iothub timed out")
                        else:
                            print("deviceClient not connected; Therefore, forwarding message to output1")
                            await client.send_message_to_output(input_message, "output1")
                    else:
                        print("Missing registrationId. forwarding message to output1")
                        await client.send_message_to_output(input_message, "output1")
                except Exception as ex:
                    print ( "Unexpected error in input1_listener: {}".format(ex) )
                    raise

        tasks = []
        tasks.append(asyncio.create_task(input1_listener(module_client)))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error {}".format(e) )
        raise

if __name__ == "__main__":
    asyncio.run(main())