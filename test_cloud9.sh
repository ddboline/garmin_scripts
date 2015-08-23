#!/bin/bash

nosetests *.py
./running_pace_plot.py
./world_record.py
