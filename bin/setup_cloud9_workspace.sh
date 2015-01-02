#!/bin/bash

sudo echo
SCRIPTDIR="${HOME}/workspace"

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools python-mpltoolkits.basemap xml2
sudo apt-get install -y python-pandas
