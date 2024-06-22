#!/bin/bash

BROKER_ADDRESS="localhost"  # Replace with your broker address
TOPIC1="iot/temp" 
TOPIC2="iot/count"                    # Replace with your topic
INTERVAL=5

while true
do
    VALUE1=$(shuf -i 1-10 -n 1)
    VALUE2=$(shuf -i 20-30 -n 1)
    mosquitto_pub -h $BROKER_ADDRESS -t $TOPIC1 -m "$VALUE1"
    mosquitto_pub -h $BROKER_ADDRESS -t $TOPIC2 -m "$VALUE2"
    echo "Published value $VALUE1 to topic $TOPIC1"
    echo "Published value $VALUE2 to topic $TOPIC2"
    sleep $INTERVAL
done
