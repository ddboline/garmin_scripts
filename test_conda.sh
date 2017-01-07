#!/bin/bash

py.test *.py
python3 ./running_pace_plot.py
python3 ./world_record.py
