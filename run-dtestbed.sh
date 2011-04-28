#!/bin/bash

# check if paramiko is installed properly
python -c "import paramiko"
if [ ${?} -eq 1 ]
then
	echo "Paramiko is not installed on your system. Program aborted."
    exit 1
fi

export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

python SisClient/Testbed/Distributed/dtestbed.py $*