# IoT Edge Gateway custom module

## Prerequisite:
- Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
- Need an [Azure Container Registry(ACR)](https://portal.azure.com/#create/Microsoft.ContainerRegistry). Our example uses ACR. Please create one if you don't have already and note the _"Login server"_, _"Registry name"_, _"User name"_, and _"password"_. You need them when you're building and publishing your module
- Install Docker in your development machine from [docker.com](https://www.docker.com/products/docker-desktop)

## Build and publish OPC UA client module
1. Copy the [provided solution](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/edge-gateway-modules/opcua-client) to your development machine and open it in VSCode
2. in [.env file](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/.env#L2-L3) replace all instance of <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_ and replace <YOUR_ACR_REGISTRY_PASSWORD> with your ACR _"password"_
3. In [module.json](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/modules/opcua_client/module.json#L5) replace <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_
4. In [deployment.template.json](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/deployment.template.json#L13-L16) replace all instance of <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_ and replace <YOUR_OPCUA_SERVER_VM_IPADDRESS> with the ipaddress of your [opcua_server VM](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/tree/main/opcua-server-sim/README.md/#L57) 
5. Right click on [deployment.template.json](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/deployment.template.json) in your vscode solution and select _"Build and Push IoT Edge Solution"_. If successful, you should see the _"opcua_client"_ package in your ACR Repositories
6. Right click on [deployment.template.json](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/deployment.template.json) in your vscode solution and select _"Generate IoT Edge Deployment Manifest"_
7. Use the [deployment.amd64.json](https://github.com/iot-for-all/iotc-opcua-iotedge-gateway/blob/main/edge-gateway-modules/opcua-client/config/deployment.amd64.json) file to create IoT Edge Gateway device template in your IoT Central application




