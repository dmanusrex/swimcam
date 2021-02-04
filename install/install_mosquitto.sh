#!/bin/bash
set -e

echo "Installing Mosquitto (this only needs to be done on the master)"

sudo apt-get update
sudo apt-get --yes install mosquitto mosquitto-dev 

# Test examples
# mosquitto_sub -t '#' -u swimcam -P swimming -v
# mosquitto_pub -t swimcam/start -m 'RESET' -u swimcam -P swimming

echo "Mosquitto installed. See SwimCam docs on how to enable security."



