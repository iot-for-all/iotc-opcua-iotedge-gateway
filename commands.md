# IoT Edge Gateway commands to handle OPC UA CRUD
You're using IoT Central preview feature **"model-less command"** to execute OPC UA CRUD commands on IoT Edge Gateway.
First, verify that you can see **"model-less command"** feature in your IoT Central app:
1. Click on your IoT Edge Gateway device to go to device detail page
2. On device detail page click on **Manage device** tab
3. Follow the instruction below if you cannot find **Command** to select in the dropdown list:
    - append _"?flights=directmethod"_ flighting option to the end of device exlorer url
    - refersh the page
    - verify **Command** is accessible under **Manage device** tab

    [<img src=./assets/15_model_less_command.png heigth="70%" width="70%">](/assets/15_model_less_command.png)

Using _"model-less command"_ you can send the following commands to IoT Edge Gateway module **"opcua_crud"** to handle OPC UA CRUD operations:
- **connect**: Connect to OPC UA server(s) once the OPC UA server(s) accessible
- **disconnect**: Disconnect from OPC UA server(s)
- **pubInterval**: Modify the OPC UA client publish events interval
- **filter**: Apply filter on OPC UA nodes specifying the node(s) to _"include"_, _"exclude"_, or _"reset"_ the filter
- **config**: Sends telemetry message containing OPC UA server(s) nodeid list

Executing commands, you need to fill up the following areas:
- **Method name**: please use one of the above command
- **Module name**: use IoT Edge Gateway module **"opcua_crud"**
- **Payload**: provide an array of structure defined below:
``` py
        {
            # Required. It also serves as deviceId in Lucid pattern
            serverId: "string",
            # Required. The OPC UA server url
            url: "string",
            # Optional. Used in Lucid pattern for provisioning child device
            modelId: "string",
            # Optional. Setting the OPC UA client publish events interval.
            # Uses default publishInterval set in desired properties if not specified
            publishInterval: "number",
            # Optional. For applying filter on OPC UA nodes
            filter: {
                # Required
                action: "include|exclude|reset"
                # Optional. No need to specify nodes array if you're using reset action
                nodes: "string[]"
            },
            # Optional. using default secrets if not provided. Meaning anonymous connection to OPC UA server
            # and use default DPS enrollment group key for provisioning the child devices
            # The value needs to be base64 encoded prior to paste in command's payload
            secrets: {
                # Optional. Server section is to define secrets to be used to connect to the OPC UA server
                server: {
                    # Required
                    type: "usrpwd|sas|cert",
                    # Required if type is usrpwd; Otherwise, optional
                    usrpwd: {
                        # Require
                        user: "string",
                        # Required
                        pwd: "string"
                    },
                    # Required if type is sas; Otherwise, optional
                    sas: {
                        # Required
                        key: "string"
                    },
                    # Required if type is cert; Otherwise, optional
                    cert: {
                        # Optional
                        thumbprint: "string",
                        # Required. Value should be the content of public PEM file
                        public: "string",
                        # Required. Value should be the content of private PEM file
                        private: "string"
                    }
                },
                # Optional. Client section is to be used for provisioning child device
                client: {
                    # Required
                    type: "sas|cert|tpm",
                    # Required if type is tpm; Otherwise, optional
                    tpm: {
                        # Required if storageRootKey not specified; Otherwise, optional
                        endorsementKey: "string",
                        # Required if endorsementKey not specified; Otherwise, optional
                        storageRootKey: "string"
                    },
                    # Required if type is sas; Otherwise, optional
                    sas: {
                        # Required
                        key: "string"
                    },
                    # Required if type is cert; Otherwise, optional
                    cert: {
                        # Optional
                        thumbprint: "string",
                        # Required. Value should be the content of public PEM file
                        public: "string",
                        # Required. Value should be the content of private PEM file
                        private: "string"
                    }
                }
            }
        }
```

To do base64 encoding the secrets value you might want to execute some thing like following python script:

``` py
    import json
    import base64

    payloads = []
    payloads.append({
        "serverId": "<YOUR_DEVICE_ID>",
        "url": "<YOUR_OPCUA_SERVER_URL>",
        "publishInterval": 800,
        "modelId": "<YOUR_OPCUA_CLIENT_MODEL_ID>",
        "secrets": {
            "client": {
                "type": "sas",
                "sas": {
                    "key": "<YOUR_OPCUA_CLIENT_SASKEY>"
                }
            }
        }
    })

    payloads.append({
        "serverId": "<YOUR_DEVICE_ID>",
        "url": "<YOUR_OPCUA_SERVER_URL>",
        "modelId": "<YOUR_OPCUA_CLIENT_MODEL_ID>",
        "secrets": {
            "client": {
                "type": "cert",
                "cert": {
                    "public": """<YOUR_PUBLIC_PEM_CONTENT>""",
                    "private": """<YOUR_PRIVATE_PEM_CONTENT>"""
                }
            }
        }
    })

    for payload in payloads:
        secrets = payload.get("secrets")
        if secrets:
            secretsStr = json.dumps(secrets, separators=(',', ':'))
            b64Encoded1 = base64.b64encode(secretsStr.encode('utf-8'))
            payload["secrets"] = b64Encoded1.decode("utf-8")

    print(">")
    print(">")
    print(">")
    print("-" * 100)
    print("{}".format(json.dumps(payloads)))
    print("-" * 100)

```