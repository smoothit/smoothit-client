#!/bin/bash
# written by Markus Guenther

for i in `ps -A | grep 'python' | cut -d ' ' -f 1`
do
	echo "Killing python process with pid:" $i
	kill -9 $i
done
