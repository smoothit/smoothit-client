#!/bin/bash

export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.
python SisClient/Testbed/PacketAnalysis/pdump.py $*
