# OPC UA Server Simulator

## Prerequisite
Need Python 3.7 or higher.  Install from [here](https://www.python.org/downloads/)

## To run
Install the needed libraries:

``` shell
pip install -r .\requirements.txt
```

Run the OPC-UA server with default config from a shell:

``` shell
python opcua_server.py
```

## To stop
Ctrl-C the python processes in there respective shells.  This is no glamour code!

## To setup Simulator
1. Create Windows Virtual Machine using the following CLI commands:
	``` shell
		#!/bin/bash
		az login

		# Setup account subscription
		az account set --subscription <YOUR_SUBSCRIPTION_NAME>

		# Make sure resource group exists
		az group create \
			--name <YOUR_RESOURCE_GROUP_NAME> \
			--location <AZURE_REGION>

		# Create a new VM running Windows
		az vm create \
			--resource-group <YOUR_RESOURCE_GROUP_NAME> \
			--name <YOUR_VM_NAME> \
			--image Win2019Datacenter \
    		--public-ip-sku Standard \
			--admin-username <YOUR_USER_NAME> \
			--admin-password <YOUR_PASSWORD>

		# Open port 4840 for OPC UA client to connect
		az vm open-port \
			--port 4840 \
			--resource-group <YOUR_RESOURCE_GROUP_NAME> \
			--name <YOUR_VM_NAME>

		# Open port 3389 for RDP connection (Remote Desktop)
		az vm open-port \
			--port 3389 \
			--resource-group <YOUR_RESOURCE_GROUP_NAME> \
			--name <YOUR_VM_NAME>
    ```
2. Connect to the Windows Virtual Machine using publicIpAddress returned in the output from your VM
	``` shell
		mstsc /v:<VM_PUBLIC_IP_ADDRESS>
	```
3. Install Python 3.7 or higher in Win10 VM from [here](https://www.python.org/downloads/)
4. Copy the [opcua_server.py](opcua_server.py), [opcua_server.json](opcua_server.json), and [requirements.txt](requirements.txt) files over to the Windows VM
5. Open the prompt command and change the directory to opcua_server.py location
6. Install the needed libraries
	``` shell
		pip install -r .\requirements.txt
	```
7. Run the OPC-UA server with default config from a shell
	``` shell
		python opcua_server.py
	```
8. Observe the opcua_server keeps logging the generated data

&nbsp;
## Credit
opcua-server-sim is an Open Source project. You can find the source code along with license information here [opcua-server-client-sim](https://github.com/iot-for-all/opcua-server-client-sim)