# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from asyncio.tasks import sleep
import json
import time
import threading
import base64
import os
import sys
sys.path.insert(0, "..")
import asyncio
import cryptocode

from opcua import Client
from azure.iot.device import Message, MethodResponse
from azure.iot.device.aio import IoTHubModuleClient

try:  
    # python 3.4
    from asyncio import JoinableQueue as Queue
except:  
    # python 3.5
    from asyncio import Queue

# global counters
TWIN_CALLBACKS = 0
RECEIVED_MESSAGES = 0
PAUSE_IN_SECOND = 15
PUBLISH_INTERVAL_MS = 500
OPAQUE = False

server_dict = {}
root_node_dict = {}
startTimer = time.process_time()

def message_handler(message):
    print("Message received on INPUT 1")
    print("the data in the message received was ")
    print(message.data)
    print("custom properties are")
    print(message.custom_properties)

async def get_twin(module_client):
    # get the twin
    twin = await module_client.get_twin()
    print("Twin document:")
    print("{}".format(twin))
    return twin

# define behavior for receiving a twin patch
async def twin_patch_handler(patch):
    print("the data in the desired properties patch was: {}".format(patch))
    print("set default publishing interval in desired properties")
    # send new reported properties
    if 'publishInterval' in patch:
        print("Reporting desired changes {}".format(patch))
        reported = { "publishInterval": patch['publishInterval'] }
        await module_client.patch_twin_reported_properties(reported)
        print("Reported twin patch")
        pubInterval = patch["publishInterval"]
        if len(server_dict) > 0:
            for k, config in server_dict.items():
                if config == None:
                    pass
                else:
                    print("changing publishing interval to %d ms" % pubInterval)
                    await config.publish_interval_update(pubInterval)
    print("Patched twin")

# Define behavior for handling methods
async def method_request_handler(method_request):
    print("Method request payload received: {}".format(method_request.payload))
    # Determine how to respond to the method request based on the method name
    if method_request.name == "connect":
        await connect_method_handler(method_request)
    elif method_request.name == "disconnect":
        await disconnect_method_handler(method_request)
    elif method_request.name == "config":
        await config_method_handler(method_request)
    elif method_request.name == "filter":
        await filter_method_handler(method_request)
    elif method_request.name == "pubInterval":
        await pubInterval_method_handler(method_request)
    else:
        payload = {"result": False, "data": "unknown method"}  # set response payload
        status = 400  # set return status code
        print("executed unknown method: " + method_request.name)

        # Send the response
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
    
async def connect_method_handler(method_request):
    result = True
    data = {}

    for item in method_request.payload:
        reported_properties = {}
        reported_properties["opcua"] = {}
        serverId = item["serverId"]
        url = item["url"]
        
        value = {}
        print("item: {}".format(item))
        for att, val in item.items():
            if val != "serverId":
                value.update({ att: val })
        
        if  value.get("publishInterval") == None:
            value.update({"publishInterval": PUBLISH_INTERVAL_MS})
            
        print("connect_method_handler: {}: {}".format(serverId, value))
        secrets = value.get("secrets")
        if secrets != None:
            value["secrets"] = cryptocode.encrypt(secrets, url.lower())
        reported_properties["opcua"].update({ serverId: value })
        print("Setting reported opcua to {}".format(reported_properties["opcua"]))
        try:
            await module_client.patch_twin_reported_properties(reported_properties)
            data.update({ serverId: { "status": 201, "data": "Scheduled connection to OPC UA server '{}'".format(serverId)}})
        except:
            data.update({ serverId: { "status": 400, "data": "Failed to schedule connection to OPC UA server '{}'".format(serverId)}})
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207
    
    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed connect")
    
async def disconnect_method_handler(method_request):
    if len(server_dict) == 0:
        print("Found no client to disconnect")
        payload = {"result": False, "data": "Found no client to disconnect"}
        status = 404
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print("executed disconnect")
        return

    result = True
    data = {}

    for item in method_request.payload:
        reported_properties = {}
        reported_properties["opcua"] = {}
        serverId = item["serverId"]
        print("Removing OPC UA server config %s from reported properties" % serverId)
        reported_properties["opcua"].update({ serverId: None })
        await module_client.patch_twin_reported_properties(reported_properties)
        
        config = server_dict.get(serverId)
        if config == None:
            print("Found no config to apply disconnect for %s" % serverId)
            data.update({config.serverId: { "status": 404, "data": "Found no config to apply disconnect for '{}'".format(serverId)}})
            result = False
        else:
            print("disconnect server: %s" % serverId)
            subscription = config.subscription
            handles = config.handles
            if subscription != None and handles != None and len(handles) > 0:
                subscription.unsubscribe(handles)
                await sleep(5)

            server_dict.pop(serverId, None)
            data.update({config.serverId: { "status": 200, "data": "Disconnect OPC UA server '{}'".format(serverId)}})
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207

    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed disconnect")
    
async def config_method_handler(method_request):
    result = True
    data = {}
    config_array = {}
    config_array["nodes"] = []
    if len(server_dict) <= 0:
        print("Found no client to retrieve the config")
        payload = {"result": False, "data": "config"}
        status = 404
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print("executed config")
        return

    for key, config in server_dict.items():
        if config == None:
            data.update({config.serverId: { "status": 404, "data": "No config found for OPC UA server '{}'".format(key)}})
            result = False
        else:
            print("Processing server config %s" % config.serverId)
            print("Variable nodes: {}".format(config.variable_nodes))
            rootNode = root_node_dict.get(config.serverId)
            if rootNode == None:
                rootNode = "Widget_Maker_1000"
            config_array["nodes"].append({"serverId": config.serverId, "serverUrl": config.url, "rootNode": rootNode, "nodes": config.variable_nodes})
            data.update({config.serverId: { "status": 200, "data": "Got OPC UA server '{}' config".format(key)}})
    
    payload = {"result": result, "data": data}
    status = 207
    
    print("      {}".format(config_array))
    msg = Message("{}".format(config_array))
    msg.content_type = "application/json"
    msg.content_encoding = "utf-8"
    msg.custom_properties = dict([("iotc_message_type", "opcua_server_config")])
    try:
        await module_client.send_message_to_output(msg, "output1")
        print("completed sending config message")
    except Exception as e:
        print("Failed to send config message: {}".format(e))
        payload = {"result": False, "data": data}
        status = 400

    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed config")
    
async def filter_method_handler(method_request):
    if len(server_dict) == 0:
        print("Found no client to apply the filter")
        payload = {"result": False, "data": "filter"}
        status = 404
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print("executed filter")
        return
    
    global startTimer
    result = True
    data = {}
    reported_properties = {}
    reported_properties["opcua"] = {}
    for item in method_request.payload:
        serverId = item["serverId"]
        config = server_dict.get(serverId)
        if config == None:
            print("Found no config to apply filter for %s" % serverId)
            data.update({config.serverId: { "status": 404, "data": "Found no config to apply filter for '{}'".format(serverId)}})
            result = False
        else:
            print("Applying filter to %s" % serverId)
            filter = item.get("filter")
            if filter == None:
                print("Found no config to apply filter for %s" % serverId)
                data.update({config.serverId: { "status": 400, "data": "Missing filter for '{}'".format(serverId)}})
                result = False
                    
            pubInterval = item.get("publishInterval")
            if pubInterval == None:
                pubInterval = config.publishInterval
                if pubInterval == None:
                    pubInterval = PUBLISH_INTERVAL_MS
            
            startTimer = time.process_time()
            action = filter["action"]
            if action == "reset":
                print("Reseting nodeid filter on server %s" % config.serverId)
                await config.reset_subscription_filter()
                
                entry = { "url": config.url, "publishInterval": pubInterval, "filter": None }
                reported_properties["opcua"].update({ config.serverId: entry })
                print("Removing reported opcua filter section {}".format(entry))
                data.update({config.serverId: { "status": 200, "data": "Reseted filter on server '{}'".format(serverId)}})
            else:
                print("Apply filter mode %s" % action)
                nodes = filter.get("nodes")
                if nodes == None or len(nodes) <= 0:
                    print("Cannot apply empty filter for %s" % serverId)
                    continue
            
                print("Filter nodes: {}".format(nodes))
                await config.apply_subscription_filter({ "action": action, "nodes": nodes})
            
                entry = { "url": config.url, "publishInterval": pubInterval, "filter": { "action": action, "nodes": nodes} }
                reported_properties["opcua"].update({ config.serverId: entry })
                print("Setting reported opcua to {}".format(entry))
                data.update({config.serverId: { "status": 200, "data": "Applied filter on server '{}'".format(serverId)}})
    
    if len(reported_properties["opcua"]) > 0:
        print("Set the state in reported properties")
        await module_client.patch_twin_reported_properties(reported_properties)
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207
    
    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed filter")
    
async def pubInterval_method_handler(method_request):
    if len(server_dict) == 0:
        print("Found no client to apply publish interval")
        payload = {"result": False, "data": "pubInterval"}
        status = 404
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print("executed pubInterval")
        return
    
    global startTimer
    result = True
    data = {}
    reported_properties = {}
    reported_properties["opcua"] = {}
    for item in method_request.payload:
        serverId = item["serverId"]
        config = server_dict.get(serverId)
        if config == None:
            print("Found no config to apply publish interval for %s" % serverId)
            data.update({config.serverId: { "status": 404, "data": "Found no config to apply publish interval for '{}'".format(serverId)}})
            result = False
        else:
            print("Applying publish interval to %s" % serverId)        
            pubInterval = item.get("publishInterval")
            if pubInterval == None:
                pubInterval = config.publishInterval
                if pubInterval == None:
                    pubInterval = PUBLISH_INTERVAL_MS
            
            startTimer = time.process_time()
            print("changing publishing interval for server %s to %d ms" % (serverId, pubInterval))
            await config.publish_interval_update(pubInterval)
            
            entry = { "publishInterval": pubInterval }
            reported_properties["opcua"].update({ config.serverId: entry })
            print("Setting reported opcua to {}".format(entry))
            data.update({config.serverId: { "status": 200, "data": "Changed publish interval on server '{}'".format(serverId)}})
    
    if len(reported_properties["opcua"]) > 0:
        print("Set the state in reported properties")
        await module_client.patch_twin_reported_properties(reported_properties)
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207
    
    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed pubInterval")

class OpcuaConfig(object):
    def __init__(self, serverId, url, opcua_client, variable_nodes) -> None:
        self.serverId = serverId
        self.secrets = None
        self.cert = None
        self.certKey = None
        self.modelId = None
        self.url = url
        self.opcua_client = opcua_client
        self.variable_nodes = variable_nodes
        self.incoming_queue = []
        self.publishInterval = None
        self.subscription = None
        self.handles = []
        self.filtered_nodes = []
        self.registrationId = serverId
        if len(variable_nodes) > 0:
            for variable_node in variable_nodes:
                self.filtered_nodes.append(variable_node)
        
    async def publish_interval_update(self, publishInterval):
        if self.publishInterval != publishInterval:
            self.publishInterval = publishInterval
            await self.apply_subscription_filter({ "action": "include", "nodes": self.filtered_nodes })


    async def apply_subscription_filter(self, filter):
        action = filter.get("action")
        nodes = filter.get("nodes")
        if action == None:
            print("Filter 'action' cannot be empty . . .")
            return
        
        if action == 'reset':
            return self.reset_subscription_filter()
        
        if nodes != None and len(nodes) > 0:
            filteredNodes = []
            for variable_node in self.variable_nodes:
                if variable_node in nodes:
                    if  action == 'include':
                        filteredNodes.append(variable_node)
                else:
                    if action == 'exclude':
                        filteredNodes.append(variable_node)
                
            handles = []
            if len(self.handles) > 0:
                self.subscription.unsubscribe(self.handles)
            
            handler = SubsriptionHandler(self)
            self.subscription = self.opcua_client.create_subscription(self.publishInterval, handler)
            for filteredNode in filteredNodes:
                node = self.opcua_client.get_node(filteredNode)
                handles.append(self.subscription.subscribe_data_change(node))
                
            self.handles = handles
            self.filtered_nodes = filteredNodes

            
    async def reset_subscription_filter(self):
        filteredNodes = []
        for variable_node in self.variable_nodes:
            filteredNodes.append(variable_node)
                
        handles = []
        if len(self.handles) > 0:
            self.subscription.unsubscribe(self.handles)
            
        handler = SubsriptionHandler(self)
        self.subscription = self.opcua_client.create_subscription(self.publishInterval, handler)
        for filteredNode in filteredNodes:
            node = self.opcua_client.get_node(filteredNode)
            handles.append(self.subscription.subscribe_data_change(node))
        
        self.handles = handles
        self.filtered_nodes = filteredNodes

class SubsriptionHandler(object):
    def __init__(self, config):
        self.config = config
        
    def datachange_notification(self, node, val, data):
        # don't try and do anything with the node as network calls to the server are not allowed outside of the main thread - so we just queue it
        incomingQueue = self.config.incoming_queue
        if incomingQueue != None:
            incomingQueue.append({"registrationId": self.config.registrationId, "secrets": self.config.secrets, "cert": self.config.cert, "certKey": self.config.certKey, "modelId": self.config.modelId, "source_time_stamp": data.monitored_item.Value.SourceTimestamp.strftime("%m/%d/%Y, %H:%M:%S"), "nodeid": node, "value": val})

    def event_notification(self, event):
        print("Python: New event", event)

# stack is redundant right now but need to move server to nodes with node class as an attribute
def walk_variables(object, variable_nodes):
    var_stack = []
    variables = object.get_children()
    for variable in variables:
        var_stack.append(variable)

    while len(var_stack) > 0:
        variable = var_stack.pop()
        children = variable.get_children()
        if len(children) == 0:
            variable_nodes.append(variable.nodeid.to_string())
            print("    - {}".format(variable.get_display_name().to_string()))
            if variable.get_data_type_as_variant_type().name == "ExtensionObject":
                # get the struct members
                for sub_var in variable.get_value().ua_types:
                    print("        - {}".format(sub_var[0]))              
        else:
            var_stack.append(variable)

def json_dump_struct(struct_value):
    value = "{"
    first = True
    for sub_var in struct_value.ua_types:
        if not first:
            value = value + ", "
        else:
            first = False
        value = value + f'"{sub_var[0]}":'
        if type(getattr(struct_value, sub_var[0])) == int or type(getattr(struct_value, sub_var[0])) == float or type(getattr(struct_value, sub_var[0])) == bool:
            value = value + str(getattr(struct_value, sub_var[0]))
        elif str(type(getattr(struct_value, sub_var[0]))) == "string":
            value = value + f'"{getattr(struct_value, sub_var[0])}"'
        elif str(type(getattr(struct_value, sub_var[0]))).startswith("<class"):
            value = value + json_dump_struct(getattr(struct_value, sub_var[0]))
    return value + "}"

async def send_to_upstream(data, module_client, customProperties):
    if module_client and module_client.connected:
        nodeid = f'"{data["nodeid"]}"'
        name = f'"{data["name"]}"'
        timestamp = f'"{data["source_time_stamp"]}"'
        valueKey = "value"

        if type(data["value"]) == int or type(data["value"]) == float or type(data["value"]) == bool:
            value = data["value"]
        elif str(type(data["value"])) == "string":
            value = f'"{data["value"]}"'
        elif str(type(data["value"])).startswith("<class"):
            value = json_dump_struct(data["value"])
            valueKey = "valueObject"

        payload = '{ "nodeid": %s, "name": %s, "source_time_stamp": %s, %s: %s}' % (nodeid, name, timestamp, valueKey, value)

        print("      %s" % (payload))
        msg = Message(payload)
        msg.content_type = "application/json"
        msg.content_encoding = "utf-8"
        
        # print("send_to_upstream CustomeProperties: {}".format(customProperties))
        for k, v in customProperties.items():
            if v != None:
                msg.custom_properties[k] = v
        
        # print("msg.custom_properties 2: {}".format(msg.custom_properties))
        try:
            await module_client.send_message_to_output(msg, "output1")
            print("completed sending message")
        except asyncio.TimeoutError:
            print("call to send message timed out")

async def incoming_queue_processor(module_client):
    global startTimer
    startTimer = time.process_time()
    while True:
        try:
            if len(server_dict) > 0:
                for key, value in server_dict.items():
                    if value == None:
                        pass
                        
                    queue = value.incoming_queue
                    client = value.opcua_client
                    if queue == None or client == None:
                        pass
                        
                    if len(queue) > 0:
                        data = queue.pop(0)
                        data["name"] = client.get_node(data["nodeid"]).get_display_name().Text
                        registrationId = data.get("registrationId")
                        properties = {}
                        properties["registrationId"] = registrationId
                        properties["modelId"] = data.get("modelId")
                        if data.get("cert") != None:
                            properties["cert"] = data["cert"]
                        if data.get("certKey") != None:
                            properties["certKey"] = data["certKey"]
                            
                        print("incoming_queue_processor: CustomeProperties: {}".format(properties))
                        # Adding secrets to properties to not to pollute the logs with secrets
                        properties["secrets"] = data.get("secrets")

                        if registrationId == None:
                            print("===>> [{}] {} - {}".format(data["source_time_stamp"], data["name"], data["value"]))
                        else:
                            print("===>> {}: [{}] {} - {}".format(registrationId, data["source_time_stamp"], data["name"], data["value"]))
                            
                        await send_to_upstream(data, module_client, properties)
                
            if time.process_time() - startTimer > 10:
                startTimer = time.process_time()
                await ping(module_client)
                
        except Exception as e:
            print("Processing incoming queue failed with exception: {}".format(e))
            pass
            
async def opcua_client_connect(value, serverId):
    global root_node_dict
    opcua_client_url = value.get("url")
    modelId = value.get("modelId")
    pubInterval = value.get("publishInterval")
    if pubInterval == None:
        pubInterval = PUBLISH_INTERVAL_MS

    filter = value.get("filter")
    if filter != None and filter.get("action") == None:
        print("Skipping filter since required 'filter.action' is missing")
        filter = None
        
    print ( "opcua_client_connect: %s" % (opcua_client_url))
    opcua_client = Client(opcua_client_url)

    try:
        # connect to the OPC-UA server
        opcua_client.session_timeout = 600000
        opcua_client.connect()
        print("connected to OPC UA server")
    except Exception as e:
        print("Connection to OPC UA server failed with exception: {}".format(e))
        return
    
    opcua_client.load_type_definitions()
    root = opcua_client.get_root_node()

    # walk the objects and variable tree
    variable_nodes = []
    objects = root.get_child(["0:Objects"]).get_children()
    for object in objects:
        root_node_name = object.get_display_name().to_string()
        print("- {}".format(root_node_name))
        # if not the Server object then walk the variables
        if root_node_name != "Server":
            root_node_dict.update({serverId: root_node_name})
            walk_variables(object, variable_nodes)
            
    config = OpcuaConfig(serverId, opcua_client_url, opcua_client, variable_nodes)
    server_dict.update({serverId: config})
    
    secrets = value.get("secrets")
    if secrets != None:
        b64Decoded = base64.b64decode(secrets.encode('utf-8'))
        secretsString = b64Decoded.decode("utf-8")
        # secrets = eval(secretsString)
        secretsJson = json.loads(secretsString)
        print("opcua_client_connect: Device secrets: {}".format(secretsJson))
        
        clientSecrets = secretsJson.get("client")
        if clientSecrets != None:
            clientSecretsType = clientSecrets.get("type")
            if clientSecretsType == "cert":
                cert = clientSecrets.get("cert")
                if cert != None:
                    publicCert = cert.get("public")
                    if publicCert != None:
                        publicFileName = "{}_public.pem".format(serverId)
                        publicFile = open("/certs/{}".format(publicFileName), "w+")
                        publicFile.write(publicCert)
                        publicFile.close()
                        config.cert = "/certs/{}".format(publicFileName)
                        print("public cert abspath: {}".format(config.cert))
                        
                    privateCert = cert.get("private")
                    if privateCert != None:
                        privateFileName = "{}_private.pem".format(serverId)
                        privateFile = open("/certs/{}".format(privateFileName), "w+")
                        privateFile.write(privateCert)
                        privateFile.close()
                        config.certKey = "/certs/{}".format(privateFileName)
                        print("private cert abspath: {}".format(config.certKey))

        config.secrets = secrets
        print("opcua_client_connect: secrets: {}".format(secrets))
    
    config.modelId = modelId
    config.publishInterval = pubInterval
    config.registrationId = None if OPAQUE else serverId
    
    if filter == None:
        # use subscription to get values
        handles = []
        handler = SubsriptionHandler(config)
        subscription = opcua_client.create_subscription(pubInterval, handler)
        for node in variable_nodes:
            node = opcua_client.get_node(node)
            handles.append(subscription.subscribe_data_change(node))

        config.publishInterval = pubInterval
        config.subscription = subscription
        config.handles = handles
    else:
        await config.apply_subscription_filter(filter)


async def ping(module_client):
    try:
        print("Ping opcua servers . . .")
        twin = await get_twin(module_client)
        print("twin: {}".format(twin))
        reported = twin["reported"]
        if 'opcua' in reported and len(reported['opcua']) > 0:
            for key, value in reported['opcua'].items():
                print("Found configuration in twin.reported for opcua server %s" % key)
                config = server_dict.get(key)
                if config == None:
                    print("Not found opcua server '%s' in cache . . ." % key)
                    secrets = value.get("secrets")
                    if secrets != None:
                        url = value.get("url")
                        value["secrets"] = cryptocode.decrypt(secrets, url.lower())
                        print("secrets: %s" % value["secrets"])
                    print("Connecting to opcua server %s" % key)
                    await opcua_client_connect(value, key)
                else:
                    try:
                        print("Sending hello message to opcua server %s" % key)
                        config.opcua_client.send_hello()
                    except Exception as e:
                        print("Ping opcus server '{}' failed with eception {}".format(key, e))
                        secrets = value.get("secrets")
                        if secrets != None:
                            url = value.get("url")
                            value["secrets"] = cryptocode.decrypt(secrets, url.lower())
                        print("Trying to re-connect to opcua server %s" % key)
                        await opcua_client_connect(value, key)
    except Exception as ex:
        print("Ping failed with eception {}".format(ex))
        pass
        
    print("Ping opcua servers completed . . .")

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IotEdge module Client for Processing OPC UA messages" )

        # The client object is used to interact with your Azure IoT hub.
        global module_client
        global startTimer
        global PUBLISH_INTERVAL_MS
        global OPAQUE
        
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()
        
        if os.getenv("opaque", "false") == "true":
            OPAQUE = True
            
        print("Opaque: {}".format(OPAQUE))
        
        twin = await get_twin(module_client)
        desired = twin["desired"]
        print("Twin properties desired:")
        print("{}".format(desired))
        if 'publishInterval' in desired and desired['publishInterval'] > 10:
            PUBLISH_INTERVAL_MS = desired['publishInterval']
                
        # set the message handler on the module
        module_client.on_message_received = message_handler
        
        # set the twin patch handler on the module
        module_client.on_twin_desired_properties_patch_received = twin_patch_handler
        
        # Set the method request handler on the module
        module_client.on_method_request_received = method_request_handler
       
        tasks = []
        tasks.append(asyncio.create_task(incoming_queue_processor(module_client)))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error {}".format(e))
        raise
        
if __name__ == "__main__":
    asyncio.run(main())