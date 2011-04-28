import unittest

from SisClient.Utils import ipaddr_utils

class IPAddressUtilsTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_ip_prefix_match(self):
        prefix_ip = "130.83.147.23/8"
        test_ip1 = "130.82.147.24"      # should match against prefix_ip
        test_ip2 = "192.168.1.1"        # should not match against prefix_ip
        self.assertTrue(ipaddr_utils.matches_ip_prefix(test_ip1, prefix_ip))
        self.assertFalse(ipaddr_utils.matches_ip_prefix(test_ip2, prefix_ip))
        
        prefix_ip2 = "130.83.54.1/16"
        test_ip3 = "130.83.55.1"
        test_ip4 = "130.82.55.1"
        self.assertTrue(ipaddr_utils.matches_ip_prefix(test_ip3, prefix_ip2))
        self.assertFalse(ipaddr_utils.matches_ip_prefix(test_ip4, prefix_ip2))
        
        prefix_ip3 = "69.32.11.4/24"
        test_ip5 = "69.32.11.5"
        test_ip6 = "69.64.11.4"
        test_ip7 = "69.32.12.5"
        self.assertTrue(ipaddr_utils.matches_ip_prefix(test_ip5, prefix_ip3))
        self.assertFalse(ipaddr_utils.matches_ip_prefix(test_ip6, prefix_ip3))
        self.assertFalse(ipaddr_utils.matches_ip_prefix(test_ip7, prefix_ip3))
        
        prefix_ip4 = "130.83.145.1/32"
        test_ip8 = "130.83.145.2"
        self.assertTrue(ipaddr_utils.matches_ip_prefix("130.83.145.1", prefix_ip4))
        self.assertFalse(ipaddr_utils.matches_ip_prefix(test_ip8, prefix_ip4))
        
if __name__ == "__main__":
    unittest.main()