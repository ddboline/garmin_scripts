#!/bin/bash

./garmin.py get
./garmin.py sync
./garmin.py year run
./unittests.py
./running_pace_plot.py
