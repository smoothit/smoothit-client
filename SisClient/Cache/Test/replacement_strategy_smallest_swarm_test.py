from SisClient.Testbed.Reporting.analyzer import logging
from SisClient.Testbed.Conditions import IsSeedingCondition
import os

def test_ratemanagement_equal(conf):
    
    if not os.path.exists("cache_tests/replacement_strategy_test/"):
        os.makedirs("cache_tests/replacement_strategy_test/")
    
    conf.set_base_directory("cache_tests/replacement_strategy_test/smallest_swarm/")
    conf.set_test_name("Ratemanagement test (smallest_swarm)")
    conf.set_timeout(100)
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)
    conf.add_file(1, "files/test1.dat")
    conf.add_file(2, "files/test2.dat")
    conf.add_file(3, "files/test3.dat")
    
    tracker = conf.add_tracker()
    
    set_peers(conf, "cache_tests/replacement_strategy_test/smallest_swarm/", "SisClient/Cache/Test/config/config4.cfg")
    
    conf.add_condition(IsSeedingCondition(2))
    conf.add_condition(IsSeedingCondition(3))
    conf.add_condition(IsSeedingCondition(4))

def set_peers(conf, basedir, cache_config):
    cache = conf.add_cache(1)
    cache.set_port(10001)
    cache.set_uprate(32)
    cache.set_downrate(32)
    cache.add_file_to_seed(1)
    cache.add_file_to_seed(2)
    cache.add_file_to_seed(3)
    cache.set_logfile(os.path.join(basedir, "logs/cache.log"))
    cache.set_neighbour_selection_mode('none')
    cache.set_birth_time(25)
    if not cache_config == None:
        cache.set_config(cache_config)
    
    client2 = conf.add_client(2)
    client2.set_port(10002)
    client2.set_uprate(1)
    client2.set_downrate(8)
    client2.add_file_to_leech(1)
    client2.set_logfile(os.path.join(basedir, "logs/client2.log"))
    client2.set_birth_time(10)
    
    client3 = conf.add_client(3)
    client3.set_port(10003)
    client3.set_uprate(1)
    client3.set_downrate(8)
    client3.add_file_to_leech(1)
    client3.set_logfile(os.path.join(basedir, "logs/client3.log"))
    client2.set_birth_time(13)
    
    client4 = conf.add_client(4)
    client4.set_port(10004)
    client4.set_uprate(1)
    client4.set_downrate(8)
    client4.add_file_to_leech(2)
    client4.set_logfile(os.path.join(basedir, "logs/client4.log"))
    client2.set_birth_time(17)
    
    client5 = conf.add_client(5)
    client5.set_port(10005)
    client5.set_uprate(1)
    client5.set_downrate(8)
    client5.add_file_to_leech(3)
    client5.set_logfile(os.path.join(basedir, "logs/client5.log"))
    client2.set_birth_time(20)
    