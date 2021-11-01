# iotc-opcua-iotedge-gateway

## connecting OPC UA devices to IoT Central using "Protocol Translation" pattern of IoT Egde Gateway
In this pattern IoT Edge Gateway is only device known in the cloud. All capabilities are part of that one device.

## OPC UA Server Simulator Setup
- Create a Win10 VM in Azure portal
- Open the following inbounds ports:
	- 4840 for OPC UA client
	- 3389 for RDP (Remote Desktop)
- Open the following outbound port
	- 4840 for OPC UA ????
- Use Remote Desktop to terminal to the VM
- Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
- Copy the [opcua-server-sim](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/iotc-opcua-iotedge-gateway/opcua-server-sim) files over to the VM
- Open the prompt command and change the directory to opcua_server.py location
- Execute "python opcua_server.py" in the command prompt
- Observe the opcua_server keeps logging the generated data
