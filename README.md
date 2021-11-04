# **Introduction**
In this step-by-step workshop you will connect OPC UA device(s) with IoT Central application via an IoT Edge Gateway device

## **Scenarios**
OPC UA devices connected to IoT Central via IoT Edge Gateway using the following patterns:
- [Protocol Translation](#protocol-translation-pattern): In this pattern IoT Edge Gateway is only device known in the cloud
- [Identity Translation](#identity-translation-pattern): here IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud

&nbsp;
## Protocol Translation pattern
In this pattern IoT Edge Gateway is only device known in the cloud. All capabilities are part of that one device.

1. Setup and run [OPC UA Server Simulator](/opcua-server-sim/readme.me#to-setup-simulator)
2. Build and publish [OPC UA client custom IoT Edge module](/edge-gateway-modules/opcua-client/readme.me)
3. Setup [IoT Central application](iotcentral.md)
4. Deploy an [IoT Edge enabled Linux VM](https://github.com/rangv/azureiotcentraledgelinux/tree/master/marketplacedeployment)
5. Confim that IoT Edge device status shows _"Provisioned"_ in your IoT Central application

    ![Azure IoT Edge VM](/assets/02_device_status.png)
6. Click on device and select _"Raw data"_ tab and verify the telemetry is flowing

    ![Azure IoT Edge VM](/assets/03_device_rawdata.png)

&nbsp;
## Identity Translation pattern
In this pattern IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud.

coming soon . . .



