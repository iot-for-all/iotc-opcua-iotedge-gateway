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
7. On the next page click on **"Relationships"**

    ![IoT Central App](/assets/10_device_template_rel.png)
8. Set the relationship by clicking on **"+ Add relationship"**, put "any" word in all 3 textboxes (Display name, Name, and Target), then click on **"Save"**, and finally **"Publish"**

    ![IoT Central App](/assets/11_device_template_publish.png)
9. Click on **"Devices"**, select the template you just created, and click on **"Create a device"** button to register an IoT Edge Gateway device to your application

    ![IoT Central App](/assets/12_device_template_select.png)
10. On the **"Create a new device"** page fill up the display name, Device ID, make sure your device template is seleted in **"Device template"** dropdown, finally click on **"Create"**

    ![IoT Central App](/assets/13_device_reg.png)
11. Go to device explorer page and confirm the device status shows as _"Registered"_

    ![IoT Central App](/assets/14_device_created.png)

5. Click on device you just registered above and open _"Connect"_ tab

    ![IoT Central App](/assets/04_device_connect_tab.png)
6. Note the **"ID scope"**, **"Device ID"**, and **"Primary key"** values. You need them later to configure IoT Edge runtime 1.2

    ![IoT Central App](/assets/01_device_connect.png)