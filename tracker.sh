#!/bin/bash
# author: Konstantin Pussep


export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

echo "Start tracker with args: '$*'"
python SisClient/Tracker/Tracker.py $*
