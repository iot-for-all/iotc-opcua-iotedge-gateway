# Create and publish OPC UA client as an IoT Edge Gateway module

## Prerequisite:
1. Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
2. Need an [Azure Container Registry(ACR)](https://portal.azure.com/#create/Microsoft.ContainerRegistry). Our example uses ACR. Please create one if you don't have already and note the _"Login server"_, _"Registry name"_, _"User name"_, and _"password"_. You need them when you're building and publishing your module
3. Install Docker in your development machine from [docker.com](https://www.docker.com/products/docker-desktop)
4. Copy the [solution provided](/opcua-client) and open it in VSCode
5. in [.env file](/modules/opcua_client/.env) replace all instance of <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_ and replace <YOUR_ACR_REGISTRY_PASSWORD> with your ACR _"password"_
6. In [module.json](/modules/opcua_client/module.json) replace <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_
7. In [deployment.template.json](deployment.template.json#L13-L16) replace all instance of <YOUR_ACR_REGISTRY_NAME> with your ACR _"Registry name"_ and replace <YOUR_OPCUA_SERVER_VM_IPADDRESS> with the ipaddress of your [opcua_server VM](/opcua-server-sim/readme.me/#L27) 
8. Right click on [deployment.template.json](deployment.template.json) in your vscode solution and select _"Build and Push IoT Edge Solution"_. If successful, you should see the _"opcua_client"_ package in your ACR Repositories
9. Right click on [deployment.template.json](deployment.template.json) in your vscode solution and select _"Generate IoT Edge Deployment Manifest"_
10. Use the [deployment.amd64.json](/config/deployment.amd64.json) file to create IoT Edge Gateway device template in your IoT Central application




