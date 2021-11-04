## Protocol Translation pattern
In this pattern IoT Edge Gateway is only device known in the cloud. All capabilities are part of that one device.

1. Setup and run [OPC UA Server Simulator](/opcua-server-sim/readme.me#to-setup-simulator)
2. Build and publish [OPC UA client custom IoT Edge module](/edge-gateway-modules/opcua-client/readme.me)
3. Setup [IoT Central application](iotcentral.md)
4. Create an [IoT Edge device template](https://github.com/rangv/azureiotcentraledgelinux/tree/master/edgemodule#create-device-template) to your application using [deployment.amd64.json](/edge-gateway-modules/opcua-client/config/deployment.amd64.json) created in step #2 above
5. [Publish the device template]() created in step #4
6. Register an [IoT Edge Gateway device](https://github.com/rangv/azureiotcentraledgelinux/tree/master/edgemodule#add-iot-edge-device) to your application
7. Deploy an [IoT Edge enabled Linux VM](https://github.com/rangv/azureiotcentraledgelinux/tree/master/marketplacedeployment). Please select **Ubuntu Server 18.04 LTS** based VM
8. Provision [VM as an IoT Edge device](https://github.com/rangv/azureiotcentraledgelinux/tree/master/edgemodule#provision-vm-as-an-iot-edge-device)
9. Go to your IoT Central application and verify that Iot Edge Gateway device status changed to _"Provisioned"_
10. Click on device and select _"Raw data"_ tab and verify the telemetry is flowing