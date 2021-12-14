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
2. Build and publish [OPC UA custom IoT Edge module](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/edge-gateway-modules/opcua-opaque/README.md)
3. Setup [IoT Central application](iotcentral.md)
4. Deploy an [IoT Edge enabled Linux VM](edgevm.md)
5. Confim that IoT Edge device status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/02_device_status.png)
6. [IoT Edge Gateway commands to handle OPC UA CRUD](commands.md)
7. Connect to your OPC UA server using the following _"model-less command"_ command as mentioned in step 6:
    - Method name: **connect**, Module name: **opcua_crud**, Payload: **[{"serverId": "opcua_client_1", "url": "opc.tcp://<YOUR_OPCUA_SERVER_VM_IPADDRESS>:4840/cnc_widget/server/"}]**
8. click on IoT Edge Gateway device and select _"Raw data"_ tab and verify the telemetry is flowing

    ![Azure IoT Edge VM](/assets/03_device_rawdata.png)

&nbsp;
## Lucid pattern
In this pattern IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud.

1. Setup and run [OPC UA Server Simulator](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/opcua-server-sim/README.md#to-setup-simulator)
2. Build and publish [OPC UA custom IoT Edge modules](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/edge-gateway-modules/opcua-lucid/README.md)
3. Setup [IoT Central application](iotcentral.md)
4. Deploy an [IoT Edge enabled Linux VM](edgevm.md)
5. Confim that IoT Edge device status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/02_device_status.png)
6. [IoT Edge Gateway commands to handle OPC UA CRUD](commands.md)
7. Connect to your OPC UA server using the following _"model-less command"_ command as mentioned in step 6:
    - Method name: **connect**, Module name: **opcua_crud**, Payload: **[{"serverId": "opcua_client_1", "url": "opc.tcp://<YOUR_OPCUA_SERVER_VM_IPADDRESS>:4840/cnc_widget/server/"}]**
8. Confim that IoT Edge device and **opcua_client_1** devices status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/15_device_status.png)
9. Confim that IoT Edge device has **opcua_client_1** device as its child device in your IoT Central application

    ![Azure IoT Edge VM](/assets/16_gateway_child_device.png)
10. Click on **opcua_client_1** device and select _"Raw data"_ tab and verify the telemetry is flowing

    ![Azure IoT Edge VM](/assets/17_device_rawdata.png)

