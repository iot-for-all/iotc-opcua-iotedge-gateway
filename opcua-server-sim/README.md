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
1. Create a Win10 VM in Azure portal
2. Open the following inbounds ports:
	- 4840 for OPC UA client
	- 3389 for RDP (Remote Desktop)
3. Open the following outbound port
	- 4840 for OPC UA server
4. Use Remote Desktop to terminal to the VM
5. Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
6. Copy the [opcua_server.py](opcua_server.py), [opcua_server.json](opcua_server.json), and [requirements.txt](requirements.txt) files over to the VM
7. Open the prompt command and change the directory to opcua_server.py location
8. Install the needed libraries
	``` shell
	pip install -r .\requirements.txt
	```
9. Run the OPC-UA server with default config from a shell
	``` shell
	python opcua_server.py
	```
10. Observe the opcua_server keeps logging the generated data

&nbsp;
## Credit
opcua-server-sim is an Open Source project. You can find the source code along with license information here [opcua-server-client-sim](https://github.com/iot-for-all/opcua-server-client-sim)