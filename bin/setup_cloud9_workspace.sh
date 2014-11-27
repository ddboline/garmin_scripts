#!/bin/bash

sudo echo
SCRIPTDIR="${HOME}/workspace"

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools python-mpltoolkits.basemap xml2

# python garmin.py build