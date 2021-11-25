# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from asyncio.tasks import sleep, wait
import json
import time
import threading
import os
import sys
sys.path.insert(0, "..")
import asyncio

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

server_dict = {}
root_node_dict = {}

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
    print("set the publishing interval for all subscription")
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
    if method_request.name == "add":
        await add_method_handler(method_request)
    elif method_request.name == "remove":
        await remove_method_handler(method_request)
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
    
async def add_method_handler(method_request):
    result = True
    data = {}
    reported_properties = {}
    reported_properties["opcua"] = {}
    for item in method_request.payload:
        serverId = item["serverId"]
        url = item["url"]
        pubInterval = item.get("publishInterval")
        if pubInterval == None:
            pubInterval = PUBLISH_INTERVAL_MS
            
        value = { "url": url, "publishInterval": pubInterval }
        if item.get("ops") != None:
            value["ops"] = item["ops"]
        
        if item.get("filter") != None:
            value["filter"] = item["filter"]
            
        value["opaque"] = item.get("opaque")
        
        # config = url_dict.get(url)
        config = server_dict.get(serverId)
        if config == None:
            await opcua_client_connect(value, serverId)
            # config = url_dict.get(url)
            config = server_dict.get(serverId)
            if config == None:
                print("Failed to connect to '%s'" % url)
                data.update({config.serverId: { "status": 400, "data": "Failed to connect to OPC UA server '{}'".format(serverId)}})
                result = False
            else:
                # url_dict.update({url: config})
                server_dict.update({serverId: config})
                data.update({config.serverId: { "status": 200, "data": "Established connection to OPC UA server '{}'".format(serverId)}})
                # send new reported properties
                reported_properties["opcua"].update({ config.serverId: value })
                print("connect to '%s'" % url)
        else:
            print("Already connected. Skipping connecting to '%s'" % url)
            data.update({config.serverId: { "status": 409, "data": "Already to connect to OPC UA server '{}'".format(serverId)}})

    if len(reported_properties["opcua"]) > 0:
        print("Setting reported opcua to {}".format(reported_properties["opcua"]))
        await module_client.patch_twin_reported_properties(reported_properties)
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207
    
    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed add")
    
async def remove_method_handler(method_request):
    if len(server_dict) == 0:
        print("Found no client to remove")
        payload = {"result": False, "data": "Found no client to remove"}
        status = 404
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print("executed remove")
        return
    
    result = True
    data = {}
    reported_properties = {}
    reported_properties["opcua"] = {}
    for item in method_request.payload:
        serverId = item["serverId"]
        config = server_dict.get(serverId)
        if config == None:
            print("Found no config to apply remove for %s" % serverId)
            data.update({config.serverId: { "status": 404, "data": "Found no config to apply remove for '{}'".format(serverId)}})
            result = False
        else:
            print("remove server: %s" % serverId)
            subscription = config.subscription
            handles = config.handles
            if subscription != None and handles != None and len(handles) > 0:
                subscription.unsubscribe(handles)
                await sleep(5)

            server_dict.pop(serverId, None)
            reported_properties["opcua"].update({ config.serverId: None })
            print("Setting reported opcua to {}".format(reported_properties["opcua"]))
            data.update({config.serverId: { "status": 200, "data": "Removed connection to OPC UA server '{}'".format(serverId)}})
        
    if len(reported_properties["opcua"]) > 0:
        await module_client.patch_twin_reported_properties(reported_properties)
    
    payload = {"result": result, "data": data}  # set response payload
    status = 207

    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    await module_client.send_method_response(method_response)
    print("executed removed")
    
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
        print("Failed to send config message: %s" % e)
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
            ops = item.get("ops")
            if ops == None:
                ops = "include"
                    
            pubInterval = item.get("publishInterval")
            if pubInterval == None:
                pubInterval = config.publishInterval
                if pubInterval == None:
                    pubInterval = PUBLISH_INTERVAL_MS
                    
            opaque = item.get("opaque")
                    
            if ops == "reset":
                print("Reseting nodeid filter on server %s" % config.serverId)
                await config.reset_subscription_filter()
                
                entry = { "url": config.url, "publishInterval": pubInterval, "opaque": opaque, "ops": None, "filter": None }
                reported_properties["opcua"].update({ config.serverId: entry })
                print("Removing reported opcua filter section {}".format(entry))
                data.update({config.serverId: { "status": 200, "data": "Reseted filter on server '{}'".format(serverId)}})
            else:
                print("Apply filter mode %s" % ops)
                nodes = item.get("filter")
                if nodes == None or len(nodes) <= 0:
                    print("Cannot apply empty filter for %s" % serverId)
                    continue
            
                print("Filter nodes: {}".format(nodes))
                await config.apply_subscription_filter(ops, nodes)
            
                entry = { "url": config.url, "publishInterval": pubInterval, "opaque": opaque, "ops": ops, "filter": nodes }
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
                    
            opaque = item.get("opaque")
            print("changing publishing interval for server %s to %d ms" % (serverId, pubInterval))
            await config.publish_interval_update(pubInterval)
            
            entry = { "publishInterval": pubInterval, "opaque": opaque }
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
    def __init__(self, serverId, url, opcua_client, variable_nodes, subsciption, handles, publishInterval, opaque) -> None:
        if opaque == None:
            opaque = True
        
        self.opaque = opaque
        self.serverId = serverId
        self.url = url
        self.opcua_client = opcua_client
        self.incoming_queue = []
        self.variable_nodes = variable_nodes
        self.subscription = subsciption
        self.handles = handles
        self.deviceId = None if opaque else serverId
        self.publishInterval = publishInterval
        self.filtered_nodes = []
        if len(variable_nodes) > 0:
            for variable_node in variable_nodes:
                self.filtered_nodes.append(variable_node)
        
    async def publish_interval_update(self, publishInterval):
        if self.publishInterval != publishInterval:
            self.publishInterval = publishInterval
            await self.apply_subscription_filter("include", self.filtered_nodes)
            
    async def apply_subscription_filter(self, ops, nodes):
        if nodes == None or len(nodes) == 0:
            if len(self.handles) > 0:
                self.subscription.unsubscribe(self.filtered_nodes)
        else:
            filteredNodes = []
            for variable_node in self.variable_nodes:
                if variable_node in nodes:
                    if  ops == 'include':
                        filteredNodes.append(variable_node)
                else:
                    if ops == 'exclude':
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
            incomingQueue.append({"deviceId": self.config.deviceId, "source_time_stamp": data.monitored_item.Value.SourceTimestamp.strftime("%m/%d/%Y, %H:%M:%S"), "nodeid": node, "value": val})

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

async def send_to_upstream(data, module_client, deviceId):
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
        if deviceId:
            msg.custom_properties.update({ "registrationId": deviceId })

        try:
            await module_client.send_message_to_output(msg, "output1")
            print("completed sending message")
        except asyncio.TimeoutError:
            print("call to send message timed out")

async def incoming_queue_processor(module_client):
    while True:
        if len(server_dict) > 0:
            try:
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
                        deviceId = data.get("deviceId")
                        if deviceId == None:
                            print("===>> [{}] {} - {}".format(data["source_time_stamp"], data["name"], data["value"]))
                        else:
                            print("===>> {}: [{}] {} - {}".format(deviceId, data["source_time_stamp"], data["name"], data["value"]))
                        
                        await send_to_upstream(data, module_client, deviceId)
            except Exception as e:
                print("Processing incoming queue failed with exception: %s" % e)
                pass
            
async def opcua_client_connect(value, serverId):
    global root_node_dict
    opcua_client_url = value.get("url")
    opaque = value.get("opaque")
    pubInterval = value.get("publishInterval")
    if pubInterval == None:
        pubInterval = PUBLISH_INTERVAL_MS
    filterNodes = value.get("filter")
    ops = value.get("ops")
    if ops == None:
        ops = "include"
    print ( "opcua_client_connect: %s" % (opcua_client_url))
    opcua_client = Client(opcua_client_url)

    try:
        # connect to the OPC-UA server
        opcua_client.session_timeout = 600000
        opcua_client.connect()
        print("connected to OPC UA server")
    except Exception as e:
        print("Connection to OPC UA server failed with exception: %s" % e)
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
            
    config = OpcuaConfig(serverId, opcua_client_url, opcua_client, variable_nodes, None, [], pubInterval, opaque)
    server_dict.update({serverId: config})
    
    if filterNodes == None:
        # use subscription to get values
        handles = []
        handler = SubsriptionHandler(config)
        subscription = opcua_client.create_subscription(pubInterval, handler)
        for node in variable_nodes:
            node = opcua_client.get_node(node)
            handles.append(subscription.subscribe_data_change(node))

        config.subscription = subscription
        config.handles = handles
    else:
        await config.apply_subscription_filter(ops, filterNodes)

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IotEdge module Client for Processing OPC UA messages" )

        # The client object is used to interact with your Azure IoT hub.
        global module_client
        global PUBLISH_INTERVAL_MS
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()
        
        twin = await get_twin(module_client)
        desired = twin["desired"]
        print("Twin properties desired:")
        print("{}".format(desired))
        if 'publishInterval' in desired and desired['publishInterval'] > 10:
            PUBLISH_INTERVAL_MS = desired['publishInterval']
        
        # Connect to opcua servers in twin reported properties if any
        reported = twin["reported"]
        print("Twin properties reported:")
        print("{}".format(reported))
        if 'opcua' in reported:
            if 'opcua' in reported and len(reported['opcua']) > 0:
                for key, value in reported['opcua'].items():
                    await opcua_client_connect(value, key)
                
        # set the message handler on the module
        module_client.on_message_received = message_handler
        
        # set the twin patch handler on the module
        module_client.on_twin_desired_properties_patch_received = twin_patch_handler
        
        # Set the method request handler on the module
        module_client.on_method_request_received = method_request_handler

        # listeners = asyncio.gather(input1_listener(module_client), twin_patch_listener(module_client), method_request_handler(module_client))
        tasks = []
        tasks.append(asyncio.create_task(incoming_queue_processor(module_client)))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise
        
if __name__ == "__main__":
    asyncio.run(main())