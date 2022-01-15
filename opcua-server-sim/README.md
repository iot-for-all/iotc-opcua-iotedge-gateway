# OPC UA Server Simulator

## To setup Simulator
1. Go to step #3, If you'd like to use an existing Windows VM
2. Create Windows Virtual Machine using the following CLI commands:
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
    ```
3. Open your VM in Azure portal click on **"Networking"** and check the following ports for being opened or not:
	- Open port 4840 for OPC UA client to connect if it's not open
		``` shell
			# Open port 4840 for OPC UA client to connect
			az vm open-port \
				--port 4840 \
				--resource-group <YOUR_RESOURCE_GROUP_NAME> \
				--name <YOUR_VM_NAME>
		```
	- Open port 3389 for RDP connection if it's not open
		``` shell
			# Open port 3389 for RDP connection (Remote Desktop)
			az vm open-port \
				--port 3389 \
				--resource-group <YOUR_RESOURCE_GROUP_NAME> \
				--name <YOUR_VM_NAME>
		```
	[<img src=../assets/18_sim_server_ports.png heigth="70%" width="70%">](../assets/18_sim_server_ports.png)
4. Connect to the Windows Virtual Machine using publicIpAddress returned in the output from your VM
	``` shell
		mstsc /v:<VM_PUBLIC_IP_ADDRESS>
	```
5. Turn off Windows defender for _"Guest or public network"_ (Please note, defender should not be disabled in production. We're turning it off for the sake of this exercise)
	- Go to **"Control Panel --> System and Security --> Windows Defender Firewall"** and click on _"Turn Windows Defender Firewall on or off"_

	  [<img src=../assets/19_server_vm_defender.png heigth="70%" width="70%">](../assets/19_server_vm_defender.png)

	- On the next page select the _"Turn off Windows Defender Firewall"_ radio button under _"Public network settings"_ section then click _"Ok"_ button

	  [<img src=../assets/20_server_vm_defender_off.png heigth="70%" width="70%">](../assets/20_server_vm_defender_off.png)

	- Verify the _"Guest or public networks"_ section looks like below:

	  [<img src=../assets/21_server_vm_defender_off_mode.png heigth="70%" width="70%">](../assets/21_server_vm_defender_off_mode.png)
	  
6. Install Python 3.7 or higher in Windows VM from [here](https://www.python.org/downloads/)
7. Make sure python and pip paths are added to _"Environment Variables"_ path
	- Currently the latest Python (3.10.0) installed under '%USERPROFILE%\AppData\Local\Programs\Python\Python310'
	- On the **"Server Manager"** > **"Local Server"** click on _"Computer name"_ to open **"System Properties"**
	- On **"System Properties"** click on _"Advanced"_ tab then click on **"Environment Variable"**
	- Add the following paths to the _"Path"_ section of _"User variables for . . ."_
		- %USERPROFILE%\AppData\Local\Programs\Python\Python310
		- %USERPROFILE%\AppData\Local\Programs\Python\Python310\Scripts
	- Adjust the above paths if python installed in different path
8. Copy the [opcua_server.py](opcua_server.py), [opcua_server.json](opcua_server.json), and [requirements.txt](requirements.txt) files over to the Windows VM
9. Open the prompt command and change the directory to opcua_server.py location
10. Install the needed libraries
	``` shell
		pip install -r .\requirements.txt
	```
11. Run the OPC-UA server with default config from a shell
	``` shell
		python opcua_server.py
	```
12. Observe the opcua_server keeps logging the generated data

## To stop
Ctrl-C the python processes in there respective shells.  This is no glamour code!

&nbsp;
## Credit
opcua-server-sim is an Open Source project. You can find the source code along with license information here [opcua-server-client-sim](https://github.com/iot-for-all/opcua-server-client-sim)