# Create and publish OPC UA client as an IoT Edge Gateway module

## Prerequisite:
1. Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
2. Install the following libraries using pip3
	```
	pip3 install opcua
	pip3 install asyncio
    pip3 install azure-iot-device
	```
3. Install Docker in your development machine from [docker.com](https://www.docker.com/products/docker-desktop)
4. Publishing your IoT Edge module, you have an option to push it to [hub.docker.com](https://hub.docker.com/) or publish it into you [Azure Container Registry(ACR)](https://portal.azure.com/#create/Microsoft.ContainerRegistry). Our example uses ACR. Please create one and note the _"Login server"_, _"Registry name"_, and _"password"_. You need them when you're creating your module
5. Copy the solution provided and open it in VSCode



