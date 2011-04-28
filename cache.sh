
export PYTHONPATH="$PYTHONPATH":BaseLib:SisClient:.

echo "Start a headless cache  with args: '$*'"
python SisClient/Cache/Cache.py $*
