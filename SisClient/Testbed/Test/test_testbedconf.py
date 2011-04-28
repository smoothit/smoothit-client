import unittest
import os
import logging

from SisClient.Testbed.TestbedConfig import TestbedConfiguration
from SisClient.Testbed.TestbedConfig import TestbedClientConfiguration
from SisClient.Testbed.Conditions import IsLeechingCondition
from SisClient.Testbed.Conditions import IsSeedingCondition

class TestbedConfigTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TestbedConfigTest("testCorrectPropagation"))
        suite.addTest(TestbedConfigTest("testNoConditionObjectPassed"))
        suite.addTest(TestbedConfigTest("testSimpleConfigWithTwoClients"))
        return suite
    
    def testNoConditionObjectPassed(self):
        conf = TestbedConfiguration("test" + os.path.normcase('/'))

        try:
            conf.add_condition(TestbedClientConfiguration(1))
        except AssertionError:
            pass
        else:
            self.fail("Expected an AssertionError")
    
    def testCorrectPropagation(self):        
        oldBaseDirectory = "test" + os.path.normcase('/')
        newBaseDirectory = "newtest" + os.path.normcase('/')
        sisUrl = "http://localhost"
        
        conf = TestbedConfiguration(oldBaseDirectory)
        client1 = conf.add_client(1)
        client2 = conf.add_client(2)
        tracker = conf.add_tracker()
        
        self.assertEquals(oldBaseDirectory, client1.get_base_directory())
        self.assertEquals(oldBaseDirectory, client2.get_base_directory())
        self.assertEquals(oldBaseDirectory, tracker.get_base_directory())
        self.assertEquals(None, client1.get_sis_url())
        self.assertEquals(None, client2.get_sis_url())
        self.assertEquals(None, conf.get_sis_url())
        
        conf.set_base_directory(newBaseDirectory, propagate=True)
        conf.set_sis_url(sisUrl, propagate=True)
        
        self.assertEquals(newBaseDirectory, client1.get_base_directory())
        self.assertEquals(newBaseDirectory, client2.get_base_directory())
        self.assertEquals(newBaseDirectory, tracker.get_base_directory())
        self.assertEquals(sisUrl, client1.get_sis_url())
        self.assertEquals(sisUrl, client2.get_sis_url())
        self.assertEquals(sisUrl, conf.get_sis_url())
    
    def testSimpleConfigWithTwoClients(self):
        baseDirectory = "test" + os.path.normcase('/') + "user"
        file = "paper.pdf"
        
        conf = TestbedConfiguration(baseDirectory)
        
        # the setting of the base directory must propagate to all
        # subsequent clients and the tracker
        conf.set_test_name("Simple test")
        conf.set_timeout(20)
    
        # add the files that you want to distribute within the test environment
        conf.add_file(1, file)
    
        # specify a tracker
        tracker = conf.add_tracker()
    
        # specify a leecher
        client1 = conf.add_client(1)
        client1.set_port(10000)
        client1.set_uprate(64)
        client1.set_downrate(64)
        client1.add_file_to_leech(1)
    
        # specify a seeder
        client2 = conf.add_client(2)
        client2.set_port(10002)
        client2.set_uprate(64)
        client2.set_downrate(64)
        client2.add_file_to_seed(1)
    
        # add some conditions the testbed shall check on
        conf.add_condition(IsLeechingCondition(1))
        conf.add_condition(IsSeedingCondition(2))

        # fetch the clients from the config
        c1 = conf.get_clients()[0]
        c2 = conf.get_clients()[1]
        cond = conf.get_conditions()
        
        self.assertEquals(20, conf.get_timeout())
        self.assertEquals("Simple test", conf.get_test_name())
        self.assertEquals(baseDirectory + os.path.normcase('/'), conf.get_base_directory())
        
        self.assertEquals(baseDirectory + os.path.normcase('/'), c1.get_base_directory())
        self.assertEquals(10000, c1.get_port())
        self.assertEquals(64, c1.get_uprate())
        self.assertEquals(64, c1.get_downrate())
        self.assertEquals(1, len(c1.get_leeching_list()))
        self.assertEquals(0, len(c1.get_seeding_list()))
        self.assertEquals(1, c1.get_leeching_list()[0])
        
        self.assertEquals(baseDirectory + os.path.normcase('/'), c2.get_base_directory())
        self.assertEquals(10002, c2.get_port())
        self.assertEquals(64, c2.get_uprate())
        self.assertEquals(64, c2.get_downrate())
        self.assertEquals(0, len(c2.get_leeching_list()))
        self.assertEquals(1, len(c2.get_seeding_list()))
        self.assertEquals(1, c2.get_seeding_list()[0])
        
        self.assertEquals(2, len(cond))
        
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    unittest.main()