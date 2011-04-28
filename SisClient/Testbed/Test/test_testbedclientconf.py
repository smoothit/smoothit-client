import unittest
import logging

from SisClient.Testbed.TestbedConfig import TestbedClientConfiguration

class TestbedClientConfTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TestbedClientConfTest("testAssertionErrorsOnInvalidArguments"))
        suite.addTest(TestbedClientConfTest("testCreateTestbedClientConf"))
        suite.addTest(TestbedClientConfTest("testCreateTestbedClientConfDefault"))
        return suite
    
    def testAssertionErrorsOnInvalidArguments(self):
        conf = TestbedClientConfiguration(1)
        
        self.assertRaises(AssertionError, conf.set_uprate, -1)
        self.assertRaises(AssertionError, conf.set_downrate, -1)
        self.assertRaises(AssertionError, conf.set_port, 1000)
        self.assertRaises(AssertionError, conf.set_peer_selection_mode, "lala")
        self.assertRaises(AssertionError, conf.set_neighbour_selection_mode, "lala")
    
    def testCreateTestbedClientConf(self):
        conf = TestbedClientConfiguration(id=1,
                                          port=8859,
                                          uprate=64,
                                          downrate=64,
                                          peerSelection="local",
                                          neighbourSelection="local")
        conf.add_file_to_leech(0)
        conf.add_file_to_leech(1)
        conf.add_file_to_seed(2)
        
        self.assertEquals(1, conf.get_id())
        self.assertEquals(8859, conf.get_port())
        self.assertEquals(64, conf.get_uprate())
        self.assertEquals(64, conf.get_downrate())
        self.assertEquals(0, conf.get_leeching_list()[0])
        self.assertEquals(1, conf.get_leeching_list()[1])
        self.assertEquals(2, conf.get_seeding_list()[0])
        self.assertEquals("local", conf.get_peer_selection_mode())
        self.assertEquals("local", conf.get_neighbour_selection_mode())
        
    def testCreateTestbedClientConfDefault(self):
        conf = TestbedClientConfiguration(2)
        
        self.assertEquals(2, conf.get_id())
        self.assertNotEquals(None, conf.get_port())
        self.assertEquals("", conf.get_base_directory())
        self.assertEquals(32, conf.get_uprate())
        self.assertEquals(32, conf.get_downrate())
        self.assertEquals(0, len(conf.get_leeching_list()))
        self.assertEquals(0, len(conf.get_seeding_list()))
        self.assertEquals("none", conf.get_peer_selection_mode())
        self.assertEquals("none", conf.get_neighbour_selection_mode())
        
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    unittest.main()