import unittest
import socket
from SisClient.RankingPolicy import RankingPolicy

munich = '129.187.143.20'
wuerzburg = '132.187.230.31'
kaiserlautern = '131.246.112.12'
darmstadt = '130.83.244.169'
karlsruhe = '129.13.214.20'

class TestGeoIPRanking(unittest.TestCase):
    def setUp(self):
        #print "Myself is ", self.me
        pass
    
    def tearDown(self):
        pass
    
    def testFromDarmstadt(self):
        own_ip = '130.83.139.168'
        self.policy = RankingPolicy.GeoIPPolicy(own_ip)
        
        ips = [own_ip]
        res = self.policy.getRankedPeers(ips)
        self.assertTrue(res[own_ip])>0
        
        ips2 = [own_ip, "193.99.144.85"]
        res = self.policy.getRankedPeers(ips2)
        self.assertTrue(res[own_ip] > res["193.99.144.85"])
        
        ips3 = [munich, wuerzburg, kaiserlautern, karlsruhe, darmstadt]
        res = self.policy.getRankedPeers(ips3)
        city = [ip for (ip,rank) in res.items() if rank == 1000]#same city
        country = [ip for (ip,rank) in res.items() if rank == 250]#same country
        self.assertEquals([darmstadt], city)
        ref = ips3
        ref.remove(darmstadt)
        self.assertEquals(set(ref), set(country))
        
    def testFromWuerzburg(self):
        own_ip = wuerzburg
        self.policy = RankingPolicy.GeoIPPolicy(own_ip)
        
        ips = [own_ip]
        res = self.policy.getRankedPeers(ips)
        self.assertTrue(res[own_ip])>0
        
        ips2 = [own_ip, "193.99.144.85"]
        res = self.policy.getRankedPeers(ips2)
        self.assertTrue(res[own_ip] > res["193.99.144.85"])
        
        # now try a list
        ips3 = [munich, wuerzburg, kaiserlautern, karlsruhe, darmstadt]
        res = self.policy.getRankedPeers(ips3)
        
        city = [ip for (ip,rank) in res.items() if rank == 1000]#same city
        region = [ip for (ip,rank) in res.items() if rank == 500]#same city
        country = [ip for (ip,rank) in res.items() if rank == 250]#same country
        
        self.assertEquals([wuerzburg], city)
        self.assertEquals([munich], region)
        ref = ips3
        ref.remove(wuerzburg)
        ref.remove(munich)
        self.assertEquals(set(ref), set(country))
    
    def testWholeList(self):
        self.policy = RankingPolicy.GeoIPPolicy('130.83.139.168') # test from Darmstadt
        
        f = open('resources/glab-ips.txt', 'r')
        list = []
        for line in f:
            #print line[:-1]
            list.append(line[:-1])
            
        ranked = self.policy.getRankedPeers(list)
        
        grouped = dict()
        
        for ref_rank in [0, 250, 500, 1000]:
            #print "For %d" % ref_rank
            group = [ip for (ip,rank) in ranked.items() if rank == ref_rank]
            #print group
            grouped[ref_rank] = group
            #print "length %d" % len(group)
            #print sorted(group)
        
        self.assertEquals(0, len(grouped[0]))
        self.assertEquals(128, len(grouped[250]))
        self.assertEquals(0, len(grouped[500]))
        self.assertEquals(24, len(grouped[1000]))
    
    def testCreation(self):
        policy = RankingPolicy.selectRankingSource('geoip')
        self.assertTrue(isinstance(policy, RankingPolicy.GeoIPPolicy))
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGeoIPRanking)
    unittest.TextTestRunner(verbosity=2).run(suite)