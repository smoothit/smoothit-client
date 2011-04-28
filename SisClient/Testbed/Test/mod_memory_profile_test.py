from SisClient.Testbed.Reporting.analyzer import *
from Conditions import *

def test_with_multiple_clients(conf):
    '''Example method that specifies a very simple test.
    '''
    # some general parameters that define our test environment
    conf.set_base_directory("MemoryBenchmarkWithMultipleClients")
    conf.set_test_name("Memory Benchmark with Multiple Clients")
    conf.set_timeout(240)
    
    # add the files that you want to distribute within the test environment
    conf.add_file(1, "BaseLib/Test/testdata.txt")
    
    # specify a tracker
    tracker = conf.add_tracker()
    
    seeder = conf.add_client(9999)
    seeder.set_port(20000)
    seeder.set_uprate(64)
    seeder.set_downrate(64)
    seeder.add_file_to_seed(1)
    
    for i in xrange(20):
        client = conf.add_client(i)
        client.set_port(10000+i*2)
        client.set_uprate(64)
        client.set_downrate(64)
        client.add_file_to_leech(1)
        
        conf.add_condition(IsSeedingCondition(i))
        
    conf.add_condition(IsSeedingCondition(9999))