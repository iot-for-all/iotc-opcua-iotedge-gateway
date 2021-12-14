# **Introduction**
In this step-by-step workshop you will connect OPC UA device(s) with IoT Central application via an IoT Edge Gateway device

## **Scenarios**
OPC UA devices connected to IoT Central via IoT Edge Gateway using the following patterns:
- [Opaque](#opaque-pattern): In this pattern IoT Edge Gateway is only device known in the cloud
- [Lucid](#lucid-pattern): here IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud

&nbsp;
## Opaque pattern
In this pattern IoT Edge Gateway is only device known in the cloud. All capabilities are part of that one device.

1. Setup and run [OPC UA Server Simulator](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/opcua-server-sim/README.md#to-setup-simulator)
2. Build and publish [OPC UA client custom IoT Edge module](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/edge-gateway-modules/opcua-opaque/README.md)
3. Setup [IoT Central application](iotcentral.md)
4. Deploy an [IoT Edge enabled Linux VM](edgevm.md)
5. Confim that IoT Edge device status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/02_device_status.png)
6. Click on your IoT Edge Gateway device to go to device detail page
7. On device detail page click on **Manage device** tab and select **Command**.
   (Please append _"?flights=directmethod"_ flighting option to the end of device exlorer url & refersh the page if you don't see the **Command**)

    ![Azure IoT Edge VM](/assets/19_model_less_command.png)
8. Using _"model-less command/c2d"_ you can instruct IoT Edge Gateway to do the following:
    - Connect to OPC UA server(s): Method name: **connect**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "url": "<OPCUA_SERVER_URL>"}]**
    - Disconnect from OPC UA server(s): Method name: **disconnect**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>"}]**
    - Modify the publish interval: Method name: **pubInterval**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "publishInterval": <SOME_INTEGER>}]**
    - Apply filter on OPC UA nodes: Method name: **filter**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "filter": { "action": "<include|exclude|reset>", "nodes": ["<nodeid1", "nodeid2", "nodeidn"]}}]**
    - Reset filter on OPC UA nodes: Method name: **filter**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "filter": { "action": "reset"}}]**
    - Get OPC UA server(s) nodeid list: Method name: **config**, Module name: **opcua_crud**
9. Connect to your OPC UA server and click on device and select _"Raw data"_ tab and verify the telemetry is flowing

    ![Azure IoT Edge VM](/assets/03_device_rawdata.png)

&nbsp;
## Lucid pattern
In this pattern IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud.

1. Setup and run [OPC UA Server Simulator](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/opcua-server-sim/README.md#to-setup-simulator)
2. Build and publish [OPC UA crud & identity custom IoT Edge modules](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/edge-gateway-modules/opcua-lucid/README.md)
3. Setup [IoT Central application](iotcentral.md)
4. Deploy an [IoT Edge enabled Linux VM](edgevm.md)
5. Confim that IoT Edge device status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/02_device_status.png)
6. Click on your IoT Edge Gateway device to go to device detail page
7. On device detail page click on **Manage device** tab and select **Command**.
   (Please append _"?flights=directmethod"_ flighting option to the end of device exlorer url & refersh the page if you don't see the **Command**)

    ![Azure IoT Edge VM](/assets/19_model_less_command.png)
8. Using _"model-less command/c2d"_ you can instruct IoT Edge Gateway to do the following:
    - Connect to OPC UA server(s): Method name: **connect**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "url": "<OPCUA_SERVER_URL>"}]**
    - Disconnect from OPC UA server(s): Method name: **disconnect**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>"}]**
    - Modify the publish interval: Method name: **pubInterval**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "publishInterval": <SOME_INTEGER>}]**
    - Apply filter on OPC UA nodes: Method name: **filter**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "filter": { "action": "<include|exclude|reset>", "nodes": ["<nodeid1", "nodeid2", "nodeidn"]}}]**
    - Reset filter on OPC UA nodes: Method name: **filter**, Module name: **opcua_crud**, Payload: **[{"serverId": "<UNIQUE_CLIENT_NAME>", "filter": { "action": "reset"}}]**
    - Get OPC UA server(s) nodeid list: Method name: **config**, Module name: **opcua_crud**
9. Connect to your OPC UA server using the following _"model-less command/c2d"_ command as mentioned in step above:
    - Method name: **connect**, Module name: **opcua_crud**, Payload: **[{"serverId": "opcua_client_1", "url": "opc.tcp://<YOUR_OPCUA_SERVER_VM_IPADDRESS>:4840/cnc_widget/server/"}]**
10. Confim that IoT Edge device and **opcua_client_1** devices status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/15_device_status.png)
11. Confim that IoT Edge device has **opcua_client_1** device as its child device in your IoT Central application

    ![Azure IoT Edge VM](/assets/16_gateway_child_device.png)
12. Click on **opcua_client_1** device and select _"Raw data"_ tab and verify the telemetry is flowing

    ![Azure IoT Edge VM](/assets/17_device_rawdata.png)

