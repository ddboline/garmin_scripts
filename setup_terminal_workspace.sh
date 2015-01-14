#!/bin/bash

apt-get update
apt-get install -y gpsbabel garmin-forerunner-tools python-mpltoolkits.basemap xml2 python-lockfile

# python garmin.py build
