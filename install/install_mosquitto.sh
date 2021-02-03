wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key
sudo apt-key add mosquitto-repo.gpg.key
cd /etc/apt/sources.list.d/
sudo wget http://repo.mosquitto.org/debian/mosquitto-buster.list
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients mosquitto-dev libmosquitto-dev

#
# Launcher
#
#  mosquitto -c mosquitto.conf -d

#
# After install test:
#

# mosquitto_sub -t '#' -u swimcam -P swimming -v
# mosquitto_pub -t swimcam/start -m 'RESET' -u swimcam -P swimming

# ensure pip is up to data and install paho Python paho library
#
sudo python3 -m pip install --upgrade pip
sudo pip3 install paho-mqtt

