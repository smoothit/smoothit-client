import unittest

from SisClient.RankingPolicy.RankingPolicy import SameIPPrefixPolicy

class TestSameIPPrefixPolicy(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testCorrectRankingAgainstSingleRefIp(self):
        reference_ip = "130.83.1.1/16"
        policy = SameIPPrefixPolicy([reference_ip])
        
        list_of_unranked_ips = ["130.83.85.17", "88.56.172.31", "127.0.0.1", "130.83.32.67"]
        dict_of_ranked_ips = policy.getRankedPeers(list_of_unranked_ips)
        self.assertEquals(dict_of_ranked_ips['130.83.85.17'], 100)
        self.assertEquals(dict_of_ranked_ips['130.83.32.67'], 100)
        self.assertEquals(dict_of_ranked_ips['88.56.172.31'], 0)
        self.assertEquals(dict_of_ranked_ips['127.0.0.1'], 0)
        
    def testCorrectRankingAgainstMultipleRefIps(self):
        reference_ips = [ "130.83.1.1/16", "83.27.1.1/8" ]
        unranked_ips = [ "130.83.27.100", "83.57.32.2", "76.32.32.12" ]
        policy = SameIPPrefixPolicy(reference_ips)
        ranked_ips = policy.getRankedPeers(unranked_ips)
        self.assertEquals(ranked_ips['130.83.27.100'], 100)
        self.assertEquals(ranked_ips['83.57.32.2'], 100)
        self.assertEquals(ranked_ips['76.32.32.12'], 0)
        
    def testDefaultIfNoRefIpsProvided(self):
        try:
            policy = SameIPPrefixPolicy()
            unranked_ips = ["1.1.1.1", "192.168.1.1"]
            ranked_ips = policy.getRankedPeers(unranked_ips)
            #self.assertEquals(ranked_ips['1.1.1.1'], 100)
            #self.assertEquals(ranked_ips['192.168.1.1'], 0)
            raise Exception("should never happen!")
        except AssertionError:
            pass
        
        
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSameIPPrefixPolicy)
    unittest.TextTestRunner(verbosity=2).run(suite)