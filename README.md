# AWS Connected Vehicle Solution Telemetry Demo

This project is designed to be used in conjunction with the [AWS Connected Mobility Solution](https://aws.amazon.com/solutions/implementations/connected-mobility-solution). While the the Connected Vehicle Solution builds the cloud framework, **this** project creates a simulation of vechicle data that can be used to send data to the cloud.  This project will build

* An AWS IoT Greengrass Group and Core device
* An AWS IoT Device


## Setup

Set up greengrass group, core, device, etc.

1. log in to Greengrass Classic (V1) console (e.g. https://console.aws.amazon.com/iot/home?region=us-east-1#/greengrass/classicIntro, but check region)
2. Click **Create Group**, **Use default group**
3. Use name `CMS-Demo-Cloud-Group`, Click **Next**, **Create group**
4. Click **Download these resources as tar.gz** -- saves in `Downloads` directory
---  Click **Choose your platform** -- opens in new tab/window ----
5. Click **Finish**


Create an EC2 or Cloud 9 instance (t2.micro is sufficient) to host a Greengrass Core. 
Follow the [guide](https://docs.aws.amazon.com/greengrass/latest/developerguide/install-ggc.html) to download the latest version of AWS IoT Greengrass. Then upload it to the Cloud9 instance with the **Upload Local Files** command from the **File** menu of the Cloud9 IDE.

Expand the Greengrass software archive and retrieve the Amazon root CA certificate by entering these commands in the terminal window of the Cloud9 instance.

```bash
sudo tar xvf <path-to-where-you-saved-greengrass>/greengrass-linux-x86-64-*.tar.gz -C /
sudo wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O /greengrass/certs/root.ca.pem
```

Upload the `tar.gz` setup file download previously during the group creation to the default directory of Cloud9 (usually, `/home/ubuntu/environment`)
1. select the 'environment' folder in the left file browser panel
2. choose File/Upload Local Files (or scp if using ssh)
3. Choose the tar.gz file from your `Downloads` or wherver you saved the {id}-setup.tar.gz package
4. Install the package from the terminal window with

```bash
cd ~/environment # or path-where-you-uploaded-the-package
sudo tar xvf *-setup.tar.gz -C /greengrass/ # substitute your {id} number if there is more than one such file
```

Add group and user 
```
sudo adduser --system ggc_user
sudo addgroup --system ggc_group
```


Start Greengrass:

```bash
sudo su -
cd /greengrass/ggc/core
./greengrassd start
```

## Create virtual telemetry device

1. clone repo to the EC2/Cloud9 instance or other computer/device where you wish to run the telemetry device. (_Hint: device code can be run under debugger on a local computer under VSCode, PyCharm, or other._)
2. install sdk and libraries 
```bash
pip3 install AWSIoTPythonSDK
pip3 install boto3
pip3 install dict_recursive_update
```


### add a device to the greengrass group

From the greengrass console,
1. select the 'CMS-Demo-Cloud-Group' if not already 
2. Click **Add Device**, **Create New Device**
3. Name the Thing 'CMS-Demo-Cloud-TCU', click **Next**, **Use Defaults**
4. Click **Download these resources as a tar.gz** and save the package in `Downloads` or wherever convenient
5. Click **Finish**
6. Deploy the group by clicking **Deploy** from the actions drop down
7. Use **Automatic Detection**
8. Wait for deployement complete -- may need to refresh page


Upload this package to the `environment/aws-connected-vechicle-solution-telemetry-demo` folder on the EC2/Cloud9 instance (or wherever you plan to run the telemetry device.)
1. Select the `aws-connected-vechicle-solution-telemetry-demo` folder from the lef side files panel
2. Choose File/Upload local files and select the {id}-setuo.tar.gz packge just downloaded

Expand the TCU thing setup package with
```bash
cd ~/environment/aws-connected-vechicle-solution-telemetry-demo
tar xvf *-setup.tar.gz
sudo wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O root.ca.pem
```

## Setup Subscriptions 

From the 'CMS-Demo-Cloud-Group' in the Greengrass section of the IoT Console:
1. Click on the Device you created above, **Click** on the ellipses and choose **Sync to Cloud**
1. Click **Subscriptions**, **Add Subscription**
2. Select **Devices** / **CMS-Demo-Cloud-TCU** for Source 
3. Select **Services** / **IoT Cloud** for Target, click **Next**
4. Enter 'vt/cvra/#' for Topic Filter and click **Next**
5. Click **Finish**
6. Add additional subscriptions for shadow service as in this table
 
    | Source | Target | Topic |
    | ------ | ------ | ----- |
    | Local Shadow Service | CMS-Demo-Cloud-TCU | $aws/things/CMS-Demo-Cloud-TCU/shadow/update/accepted |
    | Local Shadow Service | CMS-Demo-Cloud-TCU | $aws/things/CMS-Demo-Cloud-TCU/shadow/update/delta |
    | Local Shadow Service | CMS-Demo-Cloud-TCU | $aws/things/CMS-Demo-Cloud-TCU/shadow/update/rejected |
    | CMS-Demo-Cloud-TCU | Local Shadow Service | $aws/things/CMS-Demo-Cloud-TCU/shadow/update |

7. Choose **Deploy** from the Actions menu and wait for Deployment to be complete


## Start the telemetry device

In the IoT Console, Click on **Settings** and find the **Custom endpoint** near the top of the page, copy this value into an environment variable for the device/shell where you will execute the telemetry thing

```bash
export ENDPOINT={xxx}.-ats.iot.{region}.amazonaws.com 
```
_be sure to update the above with your specific endpoint_

Or use the command line client (if installed and with appropriate credentials)
```bash
export ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:data-ats --query 'endpointAddress' --output text)
```
Set env vars for credentials
```bash
export CERT=$(ls *-certificate.pem.crt)
export KEY=$(ls *-private.pem.key)
```

_Or modify as needed if you have multiple credentials. Set these vars to the specific credentials expanded from the `.tar.gz` file downloaded as part of the thing creation_


```
python3 ./telemetryThing.py -e $ENDPOINT -r root.ca.pem -c $CERT -k $KEY -n 'CMS-Demo-Cloud-TCU'
```

**the telemetry device should connect to the greengrass core and start publishing data**


## Switching Data Sources

The telemetry device will send telemetry from an S3 file (copied and cached locally). **Refer to the Data Preparation section.** 

The data source file can be changed by sending an `update` message to the 'CMS-Demo-Cloud-TCU' (or whatever your thingName is) device shadow with the `desired.file` property set to the desired file, e.g. `s3://connected-vehicle-datasource/10012.csv`.  This update message can be conviently sent from the **Things/Shadows** or the **Test** screens, which can also be used to monitor and debug the telemetry publication.

You can customize this sample update message as needed and publish to `$aws/things/{thingName}/shadow/update` with the Test client or other means.  
```json
{ 
    "state": {
      "desired": { 
        "file": "s3://<bucket_name>/<prefix>/<file_name>.csv",
        "time_col_name": "Time (s)",
        "time_scale": 1.0,
        "deviceid": "ECU-AWS-2014-V64H-YQHF9"
      } 
    }
}
```
**NOTE** the fields `file`, `time_col_name`, and `time_scale` likely all change together

| property | usage |
| ----- | ----- |
| file | csv file with rows holding telemetry samples and param names in header row |
| time_col_name | value of header column to use as timestamps -- should be numerical, not formatted |
| time_scale | scale factor to convert values of the `time_col_name` column to seconds--e.g. 1000.0 for mS, 1.0 for S |


## Data preparation

The included Notebook, `Build Dataset.ipynb` can be used or modified to create a collection of CSV files with telemetry data from a public data source. In general, a CSV file should

1. have a header row with property names (blank heads will be dropped from the telemetry publication)
2. have a column with title `Timestamp(ms)` **and be ordered by this column. (or modify the shadow as above)
3. have a `VehId` column.

The file will be read line-by-line, constructing payload messages for all the other columns with non-blank headers and publishing these messages on the topic `vt/<VehId>`.  When the end of the file is reached, the telemetry device will start again at the top. If it is desired to avoid a discontinuous jump in data, CSV files could be prepared to 'mirror' the data rows by duplicating a reverse ordered series of rows.  This would have the effect of 'back tracking' the trace, but would avoid discontinuous jumps.

Understanding this, it should be straightforward to construct a wide range of telemetry simulations. However, it is recommended that new CSV files be built from real world captures such as the VED data source so as to make GPS coordinates, speeds, etc. realistic.

## Checkout the Samples

In the Samples directory are some other applications to use this device software to send data. Follow the Simulation guide to build a small randomized sender of data that is easily piped to the telemetry device for wide range of uses.
