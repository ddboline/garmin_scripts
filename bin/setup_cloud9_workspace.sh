#!/bin/bash

sudo echo
SCRIPTDIR="${HOME}/workspace"

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools python-mpltoolkits.basemap xml2
sudo apt-get install -y python-pandas

echo "America/New_York" > timezone
sudo mv timezone /etc/timezone
sudo rm /etc/localtime
sudo ln -sf /usr/share/zoneinfo/posixrules /etc/localtime

./garmin.py get
./garmin.py year run
python unittests.py
./running_pace_plot.py 
