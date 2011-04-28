#!/bin/bash
# author: Konstantin Pussep


export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

echo "Start a headless client  with args: '$*'"
python SisClient/Client/Client.py $*
