import unittest
import logging
import sys
import os
from SisClient.Testbed.TestbedConfig import *
from SisClient.Testbed.TestbedConfigChecker import TestbedConfigurationChecker
from SisClient.Testbed.Conditions import IsLeechingCondition
from SisClient.Testbed.Conditions import IsSeedingCondition

class TestbedConfigCheckerTest(unittest.TestCase):
    
    _TMP_TEST_FILE = "testbedconfigcheckertest.tmp"
    
    def setUp(self):
        file_handle = open(self._TMP_TEST_FILE, "w")
        file_handle.write("This is just a temporary file, used for unit tests.")
        file_handle.close()
    
    def tearDown(self):
        os.remove(self._TMP_TEST_FILE)
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TestbedConfigCheckerTest("testConfWithNonExistingFile"))
        suite.addTest(TestbedConfigCheckerTest("testConfWithUnusedFiles"))
        suite.addTest(TestbedConfigCheckerTest("testCorrectConfigurationWillNotFail"))
        return suite
    
    def testCorrectConfigurationWillNotFail(self):
        baseDirectory = "test" + os.path.normcase('/') + "user"
        file = self._TMP_TEST_FILE
        
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

        ok, errors, warnings = TestbedConfigurationChecker.is_consistent(conf)
        
        self.assertTrue(ok)
        self.assertEquals(0, len(errors))
        
    def testConfWithUnusedFiles(self):
        baseDirectory = "test" + os.path.normcase('/') + "user"
        file = self._TMP_TEST_FILE
        conf = TestbedConfiguration(baseDirectory)
        
        # the setting of the base directory must propagate to all
        # subsequent clients and the tracker
        conf.set_test_name("Simple test")
        conf.set_timeout(20)
    
        # add the files that you want to distribute within the test environment
        # this should produce a warning!
        conf.add_file(1, file)
        conf.add_file(2, file)
        conf.add_file(3, file)
    
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

        ok, errors, warnings = TestbedConfigurationChecker.is_consistent(conf)
        self.assertTrue(ok)
        self.assertEquals(0, len(errors))
        self.assertEquals(1, len(warnings))
        
    def testConfWithNonExistingFile(self):
        baseDirectory = "test" + os.path.normcase('/') + "user"
        file = "AFJASLDFJASDLGKFSJADFLS.sajdFASJFASLDFJASDLFSAD"
        
        conf = TestbedConfiguration(baseDirectory)
        
        # the setting of the base directory must propagate to all
        # subsequent clients and the tracker
        conf.set_test_name("Simple test")
        conf.set_timeout(20)
    
        # add the files that you want to distribute within the test environment
        # this should produce a warning!
        conf.add_file(1, file)
        conf.add_file(2, file)
        conf.add_file(3, file)
    
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

        ok, errors, warnings = TestbedConfigurationChecker.is_consistent(conf)

        self.assertFalse(ok)
        self.assertEquals(3, len(errors))
        
if __name__ == "__main__":
    unittest.main()