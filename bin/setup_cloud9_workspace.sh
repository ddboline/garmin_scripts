#!/bin/bash

sudo echo
SCRIPTDIR="${HOME}/workspace"

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools

python garmin.py build