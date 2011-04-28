from SisClient.Testbed.Reporting.analyzer import logging
from SisClient.Testbed.Conditions import IsSeedingCondition
import os

def test_ratemanagement_equal(conf):
    
    if not os.path.exists("cache_tests/replacement_strategy_test/"):
        os.makedirs("cache_tests/replacement_strategy_test/")
    
    conf.set_base_directory("cache_tests/replacement_strategy_test/remove_content/")
    conf.set_test_name("Ratemanagement test (remove_content)")
    conf.set_timeout(20)
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)
    conf.add_file(1, "files/test1.dat")
    conf.add_file(2, "files/test2.dat")
    conf.add_file(3, "files/test3.dat")
    
    tracker = conf.add_tracker()
    
    set_peers(conf, "cache_tests/replacement_strategy_test/remove_content/", "SisClient/Cache/Test/config/config6.cfg")
    
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
    cache.set_spacelimit(1)
    if not cache_config == None:
        cache.set_config(cache_config)