#!/bin/bash
# author: Markus Guenther


export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

echo "Start testbed with args: '$*'"
python SisClient/Testbed/Testbed.py $*
