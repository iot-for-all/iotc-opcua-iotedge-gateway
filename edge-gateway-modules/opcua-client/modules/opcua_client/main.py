# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import time
import os
import sys
sys.path.insert(0, "..")
import asyncio
from six.moves import input
import threading
from opcua import Client
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubModuleClient

# global counters
TWIN_CALLBACKS = 0
RECEIVED_MESSAGES = 0
PAUSE_IN_SECOND = 15

variable_nodes = []
incoming_queue = []

class SubsriptionHandler(object):
    def datachange_notification(self, node, val, data):
        # don't try and do anything with the node as network calls to the server are not allowed outside of the main thread - so we just queue it
        incoming_queue.append({"source_time_stamp": data.monitored_item.Value.SourceTimestamp.strftime("%m/%d/%Y, %H:%M:%S"), "nodeid": node, "value": val})

    def event_notification(self, event):
        print("Python: New event", event)

# stack is redundant right now but need to move server to nodes with node class as an attribute
def walk_variables(object):
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

async def send_to_upstream(data, module_client):
    if module_client and module_client.connected:
        if type(data["value"]) == int or type(data["value"]) == float or type(data["value"]) == bool:
            value = data["value"]
        elif str(type(data["value"])) == "string":
            value = f'"{data["value"]}"'
        elif str(type(data["value"])).startswith("<class"):
            value = json_dump_struct(data["value"])

        deviceId = os.getenv(data["name"].replace('_', ''))
        nodeid = f'"{data["nodeid"]}"'
        name = f'"{data["name"]}"'
        timestamp = f'"{data["source_time_stamp"]}"'
        payload = '{ "nodeid": %s, "name": %s, "source_time_stamp": %s, "value": %s}' % (nodeid, name, timestamp, value)

        # payload = f'{{"nodeid": "{data["nodeid"]}", "name": "{data["name"]}", "source_time_stamp": "{data["source_time_stamp"]}", "value": {value}}}'
        print("      %s" % (payload))
        msg = Message(payload)
        msg.content_type = "application/json"
        msg.content_encoding = "utf-8"
        if not deviceId:
            print("Using Protocol Translation pattern, only the IoTEdge Gateway has an identity with IoT Hub")
        else:
            msg.custom_properties = dict([("deviceId", deviceId)])

        try:
            await module_client.send_message_to_output(msg, "output1")
            print("completed sending message")
        except asyncio.TimeoutError:
            print("call to send message timed out")

async def incoming_queue_processor(module_client):
    while True:
        if len(incoming_queue) > 0:
            data = incoming_queue.pop(0)
            data["name"] = opcua_client.get_node(data["nodeid"]).get_display_name().Text
            print("[{}] {} - {}".format(data["source_time_stamp"], data["name"], data["value"]))
            await send_to_upstream(data, module_client)

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IotEdge module Client for Processing OPC UA messages" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        connection_attempt_count = 0
        connected = False
        while not connected:
            try:
                # connect to the OPC-UA server
                opcua_client.session_timeout = 600000
                opcua_client.connect()
                print("connected to OPC UA server")
                connected = True
            except Exception as e:
                print("Connection to OPC UA server failed, retry %d" % (connection_attempt_count))
                connection_attempt_count += 1
                print("Trying to connect to OPC UA server in %d seconds" % PAUSE_IN_SECOND)
                time.sleep(PAUSE_IN_SECOND)
        
        opcua_client.load_type_definitions()
        root = opcua_client.get_root_node()

        # walk the objects and variable tree
        objects = root.get_child(["0:Objects"]).get_children()
        for object in objects:
            print("- {}".format(object.get_display_name().to_string()))
            # if not the Server object then walk the variables
            if object.get_display_name().to_string() != "Server":
                walk_variables(object)

        # use subscription to get values
        handler = SubsriptionHandler()
        subscription = opcua_client.create_subscription(500, handler)
        for node in variable_nodes:
            node = opcua_client.get_node(node)
            handle = subscription.subscribe_data_change(node)
        
        # need to process the incoming data outside the subscription notification so we can get information on the node           
        tasks = []
        tasks.append(asyncio.create_task(incoming_queue_processor(module_client)))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise
    finally:
        opcua_client.disconnect()

if __name__ == "__main__":
    opcua_client_url = os.environ['opcuaServerUrl']
    print ( "opcua_client_url: " + opcua_client_url)
    opcua_client = Client(opcua_client_url)
    asyncio.run(main())