#!/bin/bash

nosetests *.py
python3 ./running_pace_plot.py
python3 ./world_record.py
