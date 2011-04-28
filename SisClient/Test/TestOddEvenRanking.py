import unittest, socket
from SisClient.RankingPolicy.RankingPolicy import OddEvenPolicy

class TestOddEvenRanking(unittest.TestCase):
    '''
    Expect the same behavior as the simple SIS ranking.
    '''
    def setUp(self):
        self.policy = OddEvenPolicy()
    
    def tearDown(self):
        pass
    
    def testOddEvenRanking(self):
        #odd numbers should receive ranking of 0, even of >0
        
        ips = ["127.0.0.1"]
        self.assertEquals({"127.0.0.1":0}, self.policy.getRankedPeers(ips))
        
        ips2 = ["193.99.144.85"]
        self.assertEquals({"193.99.144.85":0}, self.policy.getRankedPeers(ips2))
        
        ips3 = ["127.0.0.1", "193.99.144.86"]
        res = self.policy.getRankedPeers(ips3)
        self.assertTrue(res["127.0.0.1"]==0)
        self.assertTrue(res["193.99.144.86"]>0)
        
        ips4 = ["193.99.144.6", "74.125.43.104"]
        for (ip, rating) in self.policy.getRankedPeers(ips4).items():
            self.assertTrue(rating > 0)
    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOddEvenRanking)
    unittest.TextTestRunner(verbosity=2).run(suite)