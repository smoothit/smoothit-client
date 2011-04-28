import unittest
import logging

from SisClient.Testbed.TestbedConfig import TestbedTrackerConfiguration

class TestbedTrackerTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TestbedTrackerTest("testAssertionErrorsOnInvalidArguments"))
        suite.addTest(TestbedTrackerTest("testCreateTestbedTracker"))
        suite.addTest(TestbedTrackerTest("testCreateTestbedTrackerDefault"))
        suite.addTest(TestbedTrackerTest("testCreateTestbedTrackerWithCorrectURL"))
        suite.addTest(TestbedTrackerTest("testCreateTestbedTrackerWithIncorrectURL"))
        return suite
   
    def testAssertionErrorsOnInvalidArguments(self):
        conf = TestbedTrackerConfiguration()
        
        self.assertRaises(AssertionError, conf.set_uprate, -1)
        self.assertRaises(AssertionError, conf.set_downrate, -1)
        self.assertRaises(AssertionError, conf.set_url, "http://localhost:1000/announce")
        self.assertRaises(AssertionError, conf.set_piece_length, 0)
    
    def testCreateTestbedTracker(self):
        trackerConfig = TestbedTrackerConfiguration(64, 
                                                    64, 
                                                    "http://localhost:8859/announce", 
                                                    1000)
        
        self.assertEquals(64, trackerConfig.uprate)
        self.assertEquals(64, trackerConfig.downrate)
        self.assertEquals("http://localhost:8859/announce", trackerConfig.get_url())
        self.assertEquals(1000, trackerConfig.get_piece_length())
        
    def testCreateTestbedTrackerDefault(self):
        trackerConfig = TestbedTrackerConfiguration()
        
        self.assertEquals(32, trackerConfig.get_uprate())
        self.assertEquals(32, trackerConfig.get_downrate())
        self.assertEquals("http://localhost:8859/announce", trackerConfig.get_url())
        self.assertEquals(32768, trackerConfig.get_piece_length())
        
    def testCreateTestbedTrackerWithCorrectURL(self):
        trackerConfig = TestbedTrackerConfiguration()
        self.assertEquals("http://localhost:8859/announce", trackerConfig.get_url())
        new_url = "http://anything.com:8859/announce"
        trackerConfig.set_url(new_url)
        self.assertEquals(new_url, trackerConfig.get_url())
        
    def testCreateTestbedTrackerWithIncorrectURL(self):
        trackerConfig = TestbedTrackerConfiguration()
        correct_url = "http://localhost:8859/announce"
        self.assertEquals(correct_url, trackerConfig.get_url())
        # the following call should not change the URL, since it is not
        # compliant to the required URL pattern
        trackerConfig.set_url("http://lala/announce")
        self.assertEquals(correct_url, trackerConfig.get_url())
        
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    unittest.main()