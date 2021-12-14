# IoT Central Application Setup

1. Create an [IoT Central application](https://apps.azureiotcentral.com/build)
2. Click on **"Create app"**

    ![IoT Central App](/assets/05_central_app_create.png)
3. Fill up the required information and click **"Create"**

    ![IoT Central App](/assets/06_central_app_create.png)
3. Click on **"Device template"** then **"+ New"**start creating an IoT Edge device template 

    ![IoT Central App](/assets/07_device_template.png)
4. On the **"Select type"** page click on **"Azure IoT Edge"** tile

    ![IoT Central App](/assets/08_device_template_type.png)
5. Click **"Next: Customize"** and provide a name in **"Device template name"** textbox, ckeck _"This is a gateway device"_ checkbox, and click on **"Browse"** button to upload the [deployment.amd64.json](/edge-gateway-modules/opcua-client/config/deployment.amd64.json) you created previously then click **"Next: Review"**

    ![IoT Central App](/assets/09_device_template_upload.png)
6. Click on **"Create"** button on **"Review"** page
7. Add the following capabilities to **opcua_crud** module:
    - Display name: **publishInterval**, Name: **publishInveral**, Capability type: **Property**, Schema: **Double**, Writable: **On**
    - Display name: **nodeid**, Name: **nodeid**, Capability type: **Telemetry**, Schema: **String**
    - Display name: **name**, Name: **name**, Capability type: **Telemetry**, Schema: **String**
    - Display name: **source_time_stamp**, Name: **source_time_stamp**, Capability type: **Telemetry**, Schema: **String**
    - Display name: **value**, Name: **value**, Capability type: **Telemetry**, Schema: **Double**
    - Display name: **valueObject**, Name: **valueObject**, Capability type: **Telemetry**, Schema: **Object** 
        - click on **Define** to add following object's properties:
            - Display name: **x**, Name: **x**, Schema: **Float**
            - Display name: **y**, Name: **y**, Schema: **Float**
            - Display name: **z**, Name: **z**, Schema: **Float**
        - Click **Apply**
    - Click on **Save**

    ![IoT Central App](/assets/10_device_template_capabilities.png)
8. On the next page click on **"Relationships"**

    ![IoT Central App](/assets/10_device_template_rel.png)
9. Set the relationship by clicking on **"+ Add relationship"**, put "any" word in all 3 textboxes (Display name, Name, and Target), then click on **"Save"**, and finally **"Publish"**

    ![IoT Central App](/assets/11_device_template_pub.png)
10. Click on **"Devices"**, select the template you just created, and click on **"Create a device"** button to register an IoT Edge Gateway device to your application

    ![IoT Central App](/assets/12_device_template_select.png)
11. On the **"Create a new device"** page fill up the display name, Device ID, make sure your device template is seleted in **"Device template"** dropdown, finally click on **"Create"**

    ![IoT Central App](/assets/13_device_reg.png)
12. Go to device explorer page and confirm the device status shows as _"Registered"_

    ![IoT Central App](/assets/14_device_created.png)

13. Click on device you just registered above and open _"Connect"_ tab

    ![IoT Central App](/assets/04_device_connect_tab.png)
14. Note the **"ID scope"**, **"Device ID"**, and **"Primary key"** values. You need them later to configure IoT Edge runtime 1.2

    ![IoT Central App](/assets/01_device_connect.png)