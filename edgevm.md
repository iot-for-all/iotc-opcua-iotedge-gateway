# Deploy Azure IoT Edge Enabled Linux VM
Creating **Ubuntu Server 18.04 LTS** based virtual machine will install the latest Azure IoT Edge runtime and its dependencies on startup, and makes it easy to connect to your IoT Central application via Device Provisioning Service (DPS)

## Requirements
- Install [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Install [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)
- Create [IoT Central application](iotcentral.md)

## Create a virtual machine running Ubuntu 18.04 LTS
1. Execute the following in Azure CLI
    ``` shell
    #!/bin/bash
    az login

    # Let az know which subscription should be used
    az account set --subscription <YOUR_SUBSCRIPTION_NAME>

    # Make sure resource group exists
    az group create \
        --name <YOUR_RESOURCE_GROUP_NAME> \
        --location <AZURE_REGION>

    # Create a new VM running Ubuntu 18.04 LTS
    az vm create \
        --resource-group <YOUR_RESOURCE_GROUP_NAME> \
        --name <YOUR_VM_NAME> \
        --image UbuntuLTS \
        --admin-username <YOUR_USER_NAME> \
        --admin-password <YOUR_PASSWORD> \
        --size Standard_D2s_v3

    # Open port 22 for SSH
    az vm open-port \
        --port 22 \
        --resource-group <YOUR_RESOURCE_GROUP_NAME> \
        --name <YOUR_VM_NAME>
    ```
2. SSH to VM using [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/) and your VM ipAddress (get the ipAddress in portal.azure.com)
3. Execute the following script in SSH shell to install and configure IoT Edge runtime 1.2
    ```Command arguments
    wget https://github.com/Azure/iot-edge-config/releases/latest/download/azure-iot-edge-installer.sh -O azure-iot-edge-installer.sh \
    && chmod +x azure-iot-edge-installer.sh \
    && sudo -H ./azure-iot-edge-installer.sh -s <IDScope> -r <DeviceID> -k <PrimaryKey> \
    && rm -rf azure-iot-edge-installer.sh
    ```
    Get the **IDScope**, **DeviceID**, and **PrimaryKey** from your IoT Central application from _"Device connection"_ page

    ![Azure IoT Edge VM](/assets/01_device_connect.png)
4. Deployment completes in around 3 minutes.
5. Confirm Azure Edge Runtime is installed on the VM by executing the following command in SSH shell
    ```Linux
    iotedge version
    ```
6. Apply the configuration and restart IoT Edge runtime by executing the following command in SSH shell
    ```Linux
    sudo iotedge config apply
    ```
7. Check IoT Edge status
    ```Linux
    sudo iotedge list
    ```