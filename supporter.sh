#!/bin/bash

export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

echo "Start tracker with args: '$*'"
python SisClient/TrackerExt/Supporter.py $*
