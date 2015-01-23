#!/bin/bash

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools xml2
# sudo apt-get install -y python-mpltoolkits.basemap
sudo apt-get install -y python-pandas python-lockfile

./test_cloud9.sh
