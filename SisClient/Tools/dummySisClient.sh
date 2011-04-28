#!/bin/bash
# created by Konstantin Pussep

# default SIS url
#URL=http://127.0.0.1:8080/sis/ClientEndpoint?wsdl


# set python path
export PYTHONPATH="$PYTHONPATH":lib:.

python SisClient/Tools/DummySisClient.py $*
#python SisClient/Tools/DummySisClient.py http://127.0.0.1:8080/sis/ClientEndpoint?wsdl SisClient/Test/test_ips.txt
