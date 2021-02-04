#!/bin/bash
set -e

# verify internet connection
curl https://www.github.com

if [ $? -ne 0 ]; then
echo "Unable to connect to the internet.  Please check your connection and try again."
exit -1
fi

sudo apt-get update

# install dependencies

sudo apt-get --yes install meson ninja-build build-essential autotools-dev libglib2.0-dev pkg-config python3 git gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav libglib2.0-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstrtspserver-1.0-dev gir1.2-gst-rtsp-server-1.0 libgstrtspserver-1.0-0 libmosquitto-dev mosquitto-clients

# Ensure pip3 is installed/up to date and install the paho mqtt client

sudo python3 -m pip install --upgrade pip
sudo pip3 install paho-mqtt

# success
cd ../
echo "Swimcam dependencies were successfully installed..."

