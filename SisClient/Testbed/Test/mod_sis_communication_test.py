from analyzer import *
from Conditions import *

def test_sis_minimal(conf):
    '''This is a very minimalistic test that is used to check if the SIS
       server is working as it should be.
    '''
    conf.set_base_directory("test_sis_minimal")
    conf.set_test_name("SIS Test with two clients")
    conf.set_timeout(45)
    
    conf.add_file(1, "BaseLib/Test/testdata.txt")
    
    sisUrl = "http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"
    
    tracker = conf.add_tracker()
    
    client1 = conf.add_client(1)
    client1.set_port(10000)
    client1.set_uprate(64)
    client1.set_downrate(64)
    client1.add_file_to_leech(1)
    client1.set_logfile("test_sis_minimal/client1.log")
    client1.set_sis_url(sisUrl)
    client1.set_peer_selection_mode("simple")
    client1.set_neighbour_selection_mode("simple")
    
    client2 = conf.add_client(2)
    client2.set_port(10002)
    client2.set_uprate(64)
    client2.set_downrate(64)
    client2.add_file_to_seed(1)
    client2.set_logfile("test_sis_minimal/client2.log")
    client2.set_sis_url(sisUrl)
    client2.set_peer_selection_mode("simple")
    client2.set_neighbour_selection_mode("simple")
    
    conf.add_condition(IsLeechingCondition(1))
    conf.add_condition(IsSeedingCondition(2))
    conf.add_condition(IsSeedingCondition(1))