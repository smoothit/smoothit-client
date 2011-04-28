cd ../../../../
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/replacement_strategy_fifo_test
sleep 5
killall python
sleep 5
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/replacement_strategy_smallest_swarm_test
sleep 5
killall python
sleep 5
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/replacement_strategy_unviable_test
sleep 5
killall python
sleep 5
sh run-testbed.sh --module=SisClient/Testbed/Cache/Test/replacement_strategy_remove_content
sleep 5
killall python
sleep 5