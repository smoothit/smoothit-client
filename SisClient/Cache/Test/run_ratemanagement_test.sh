cd ../../../../
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/ratemanagement_test
sleep 5
killall python
sleep 5
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/ratemanagement_test_on_demand
sleep 5
killall python
sleep 5
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/ratemanagement_test_swarm_size
sleep 5
killall python
sleep 5