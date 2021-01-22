#!/bin/bash

export THING_NAME='thingname'

cd  aws-connected-mobility-solution-telemetry-device-demo 

export ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:data-ats --query 'endpointAddress' --output text)
export CERT=$(ls *-certificate.pem.crt)
export KEY=$(ls *-private.pem.key)

echo $ENDPOINT
echo $CERT
echo $KEY

./samples/gen.py >generated_data &
python3 ./telemetryThing.py -e $ENDPOINT -r root.ca.pem -c $CERT -k $KEY -n $THING_NAME