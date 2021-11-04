import sys
from opcua.ua.uaprotocol_auto import UadpWriterGroupMessageDataType, UserIdentityToken

from opcua.ua.uatypes import VariantType
sys.path.insert(0, "..")
import time
import json
import random

from opcua import ua, Server
from opcua.common.type_dictionary_buider import DataTypeDictionaryBuilder, get_ua_class

value_update_frequency = 5

def getdelta(type, function):
    delta_value = 0
    if type.startswith("Int"):
        delta_value = 1
    elif type.startswith("Float"):
        delta_value = random.random()
    if function == "inc":
        delta_value = delta_value * 1
    elif function == "rnd_inc":
        if random.randint(0, 1) == 1:
            delta_value = delta_value * 1
        else:
            delta_value = 0
    elif function == "dec":
        delta_value = delta_value * -1
    elif function == "rnd_dec":
        if random.randint(0, 1) == 1:
            delta_value = delta_value * -1
        else:
            delta_value = 0
    elif function == "rnd_walk":
        if random.randint(0, 1) == 1:
            delta_value = delta_value * -1
    return delta_value

if __name__ == "__main__":
    # load the config file
    f = open('opcua_server.json',)
    config = json.load(f)
    f.close()

    # setup our server
    server = Server()
    server.set_endpoint(config["server"]["endpoint"])

    # setup our own namespace, not really necessary but should as spec
    uri = config["server"]["uri"]
    idx = server.register_namespace(uri)

    # custom structure storage
    datatype_builder = DataTypeDictionaryBuilder(server, idx, uri, 'customStructures')

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # build the custom structures needed
    custom_types = {}
    for struct in config["structures"]:
        custom_types[struct["name"]] = datatype_builder.create_data_type(struct["name"])
        for field in struct["fields"]:
            custom_types[struct["name"]].add_field(field["name"], ua.VariantType.__dict__.get(field["type"]))

    # save and load the custom structures into the server
    datatype_builder.set_dict_byte_string()
    server.load_type_definitions()

    # populating our address space
    variable_states = []
    for object in config["objects"]:
        new_obj = objects.add_object(idx, object["name"])

        # create the variables in the object
        for variable in object["variables"]:
            new_variable_state = variable
            variable_states.append(new_variable_state)

            new_variable_state["var"] = None
            datatype = ua.VariantType.__dict__.get(variable["type"])
            if datatype:
                new_variable_state["var"] = new_obj.add_variable(idx, variable["name"], variable["value"], datatype)
            else:
                # assume this is a custom datatype/struct
                new_variable_state["var"] = new_obj.add_variable(idx, variable["name"], ua.Variant(None, ua.VariantType.Null), datatype=custom_types[variable["type"]].data_type)
            if variable["writable"]:
                new_variable_state["var"].set_writable()

    # start the server
    server.start()
    
    try:
        count = 0
        while True:
            for variable_state in variable_states:
                delta_value = getdelta(variable_state["type"], variable_state["function"])
                datatype = ua.VariantType.__dict__.get(variable_state["type"])
                if datatype:
                    variable_state["value"] = variable_state["value"] + delta_value
                else:
                    variable_state["value"] = get_ua_class(variable_state["type"])()
                    for sub_vars in variable_state["value"].ua_types:
                        current_val = getattr(variable_state["value"], sub_vars[0])
                        delta_value = getdelta(sub_vars[1], variable_state["function"])
                        setattr(variable_state["value"], sub_vars[0][0], current_val + delta_value)

                if variable_state["writable"]:
                    variable_state["var"].set_value(variable_state["value"])
                print("--->>>", variable_state)
            time.sleep(value_update_frequency)
    finally:
        #close connection, remove subcsriptions, etc
        server.stop()