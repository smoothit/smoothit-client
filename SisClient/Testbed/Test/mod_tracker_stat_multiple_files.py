from SisClient.Testbed.Reporting.analyzer import *
from Conditions import *

def test_minimal(conf):
    conf.set_base_directory("test_with_two_clients")
    conf.set_test_name("Tracker statistics test")
    conf.set_timeout(200)
    
    conf.add_file(1, "BaseLib/Test/testdata.txt")
    conf.add_file(2, "BaseLib/Test/API/file2.wmv")
    conf.add_file(3, "BaseLib/Test/API/file.wmv")
    
    tracker = conf.add_tracker()
    
    client1 = conf.add_client(1)
    client1.set_port(10000)
    client1.set_uprate(100)
    client1.set_downrate(100)
    client1.add_file_to_leech(1)
    client1.add_file_to_leech(2)
    client1.add_file_to_leech(3)
    client1.set_logfile("test_with_two_clients/client1.log")
    
    client2 = conf.add_client(2)
    client2.set_port(10002)
    client2.set_uprate(100)
    client2.set_downrate(100)
    client2.add_file_to_seed(1)
    client2.add_file_to_seed(2)
    client2.add_file_to_seed(3)
    client2.set_logfile("test_with_two_clients/client2.log")