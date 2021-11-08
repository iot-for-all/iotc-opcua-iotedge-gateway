import json
import time
import os
import sys
sys.path.insert(0, "..")
import base64
import hmac
import hashlib
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.iot.device import MethodResponse
from azure.iot.device import exceptions

# device settings - FILL IN YOUR VALUES HERE
provisioning_host = "global.azure-devices-provisioning.net"
scope_id = os.environ['dpsScopeId']
group_symmetric_key = os.environ['dpsEnrollmentGroupSaskey']

model_id = os.environ['modelId']
gateway_id = os.environ['gatewayId']

await_timeout = 4.0
use_websockets = True
max_connection_attempt = 3

connStrings = {}

# derives a symmetric device key for a device id using the group symmetric key
def derive_device_key(device_id, group_symmetric_key):
    message = device_id.encode("utf-8")
    signing_key = base64.b64decode(group_symmetric_key.encode("utf-8"))
    signed_hmac = hmac.HMAC(signing_key, message, hashlib.sha256)
    device_key_encoded = base64.b64encode(signed_hmac.digest())
    return device_key_encoded.decode("utf-8")

# connect is not optimized for caching the IoT Hub hostname so all connects go through Device Provisioning Service (DPS)
# a strategy here would be to try just the hub connection using a cached IoT Hub hostname and if that fails fall back to a full DPS connect
async def connect(deviceId):
    global connStrings

    if deviceId in connStrings:
        connStr = connStrings[deviceId]
        if connStr:
            try:
                device_client = IoTHubDeviceClient.create_from_connection_string(connStr, websockets=use_websockets)
                await device_client.connect()
                return device_client
            except Exception as ex:
                print("Cached connection failed for device: %s, %s" % (deviceId, ex))
                connStrings.pop(deviceId)

    connected = False
    device_symmetric_key = derive_device_key(deviceId, group_symmetric_key)
    connection_attempt_count = 0
    while not connected and connection_attempt_count < max_connection_attempt:
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host=provisioning_host,
            registration_id=deviceId,
            id_scope=scope_id,
            symmetric_key=device_symmetric_key,
            websockets=use_websockets
        )

        provisioning_device_client.provisioning_payload = '{"iotcGateway":{"iotcGatewayId":"%s"},"iotcModelId":"%s"}' % (gateway_id, model_id)
        print("----- DPS Provisioning payload:" + provisioning_device_client.provisioning_payload)
        registration_result = None

        try:
            registration_result = await provisioning_device_client.register()
        except (exceptions.CredentialError, exceptions.ConnectionFailedError, exceptions.ConnectionDroppedError, exceptions.ClientError, Exception) as e:
            print("DPS registration exception: " + e)
            connection_attempt_count += 1

        if registration_result.status == "assigned":
            dps_registered = True

        if dps_registered:
            device_client = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=device_symmetric_key,
                hostname=registration_result.registration_state.assigned_hub,
                device_id=registration_result.registration_state.device_id,
                websockets=use_websockets
            )

        try:
            await device_client.connect()
            connStrings[deviceId] = "HostName=%s;DeviceId=%s;SharedAccessKey=%s" % (registration_result.registration_state.assigned_hub, registration_result.registration_state.device_id, device_symmetric_key)
            connected = True
            print("connected to central")
        except Exception as e:
            print("Connection failed, retry %d of %d" % (connection_attempt_count, max_connection_attempt))
            connection_attempt_count += 1

    return device_client

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )
        print ("env variables: %s, %s, %s" % (scope_id, group_symmetric_key, gateway_id))

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        # define behavior for receiving an input message on input1
        async def input1_listener(client):
            while True:
                try:
                    input_message = await client.receive_message_on_input("input1")
                    message = input_message.data
                    size = len(message)
                    message_text = message.decode('utf-8')
                    print ( "    Data: <<<%s>>> & Size=%d" % (message_text, size) )
                    custom_properties = input_message.custom_properties
                    print ( "    Properties: %s" % custom_properties )
                    deviceId = custom_properties['$.cdid']
                    print ( "    deviceId: %s" % deviceId )
                    deviceClient = await connect(deviceId)
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
                        print("forwarding mesage to output1")
                        await client.send_message_to_output(input_message, "output1")
                except Exception as ex:
                    print ( "Unexpected error in input1_listener: %s" % ex )
                    raise

        tasks = []
        tasks.append(asyncio.create_task(input1_listener(module_client)))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    asyncio.run(main())