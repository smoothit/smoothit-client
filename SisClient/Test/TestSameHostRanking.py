import unittest, socket
from SisClient.RankingPolicy.RankingPolicy import SameHostPolicy

class TestSameHostRanking(unittest.TestCase):
    def setUp(self):
        sys_name = socket.gethostname()
        # IP adress
        self.me = socket.gethostbyname(sys_name)
        self.policy = SameHostPolicy()
        #print "Myself is ", self.me
    
    def tearDown(self):
        pass
    
    def testSameHost(self):
        
        ips = ["127.0.0.1"]
        res = self.policy.getRankedPeers(ips)
        self.assertTrue(res["127.0.0.1"])>0
        
        ips2 = ["193.99.144.85"]
        res = self.policy.getRankedPeers(ips2)
        self.assertTrue(res["193.99.144.85"]==0)
        
        ips3 = ["127.0.0.1", "193.99.144.85"]
        res = self.policy.getRankedPeers(ips3)
        self.assertTrue(res["193.99.144.85"]==0)
        self.assertTrue(res["127.0.0.1"])>0
        
        ips4 = ["193.99.144.85", self.me, "74.125.43.104"]
        res = self.policy.getRankedPeers(ips4)
        self.assertTrue(res[self.me]>0, str(res))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSameHostRanking)
    unittest.TextTestRunner(verbosity=2).run(suite)