# **iotc-opcua-iotedge-gateway**

## OPC UA Server Simulator Setup
1. Create a Win10 VM in Azure portal
2. Open the following inbounds ports:
	- 4840 for OPC UA client
	- 3389 for RDP (Remote Desktop)
3. Open the following outbound port
	- 4840 for OPC UA server
4. Use Remote Desktop to terminal to the VM
5. Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
6. Copy the [opcua-server-sim](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/iotc-opcua-iotedge-gateway/opcua-server-sim) files over to the VM
7. Open the prompt command and change the directory to opcua_server.py location
8. Install the following libraries using pip3
	```
	pip3 install opcua
	pip3 install asyncio
	```
9. Execute "python opcua_server.py" in the command prompt
10. Observe the opcua_server keeps logging the generated data

## IoT Edge Gateway Device Setup

# **Scenarios**
### OPC UA devices connected to IoT Central via IoT Edge Gateway using the following patterns:
### 1. ***Protocol Translation***: In this pattern IoT Edge Gateway is only device known in the cloud. All capabilities are part of that one device.

1. Setup and run [OPC UA Server Simulator](#OPC-UA-Server-Simulator-Setup)
2. Create and publish OPC UA client custom IoT Edge module by following steps documented in [edge-gateway-modules](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/iotc-opcua-iotedge-gateway/edge-gateway-modules)
3. Create an IoT Central application [IoT Central](https://docs.microsoft.com/en-us/learn/modules/connect-iot-edge-device-to-iot-central/)
4. Add an IoT Edge Gateway device template to your application using the deployment manifest.json created in step #2 above
5. Publish the device template
6. Add an IoT Edge device to your IoT Central application
7. Deploy an IoT Edge enabled Linux VM
```
```
### 2. ***identity Translation***: In this pattern IoT Edge Gateway (OPC UA client) and leaf devices (OPC UA server) known in the cloud.



