import unittest, socket, logging, sys
from SisClient.RankingPolicy.Communicator import Communicator
from TestOddEvenRanking import TestOddEvenRanking

SIS_URL="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"
#SIS_URL="http://130.83.244.162:8080/sis/ClientEndpoint?wsdl"

class TestSISRanking(TestOddEvenRanking):

    def _tryRanking(self, iplist):
        rated = self.policy.getRankedPeers(iplist)
        #print rated
        self.assertEqual(2, len(rated.items()))
        for ip in iplist:
            self.assertTrue(rated.has_key(ip))
        return rated

    def setUp(self):
        self.policy = Communicator(SIS_URL, simple=True)
    
    def tearDown(self):
        pass
    
    def testAdd(self):
        # test the add-functionality of the Web-Service
        sum = self.policy._get_sum(10, 9)
        self.assertEquals(19, sum)
    
    def testSimple(self):
        #build request
        rated = self._tryRanking(iplist = ['209.34.91.45', '81.19.23.42'])
        self.assertTrue(rated['81.19.23.42']>rated['209.34.91.45'])
        
    def testRegular(self):
        #print "IGNORE Regular SIS ranking TEST CASE FOR NOW, since regular SIS ranking is broken in the server,\n see http://dev.kom.e-technik.tu-darmstadt.de/redmine/issues/show/700 for details"
        #return
        #build request #TODO: activate once the issue 
        self.policy.simple = False # enable regular ranking
        self._tryRanking(iplist = ['209.34.91.45', '81.19.23.42'])
        
    
    def testCaching(self):
        self.assertEqual(0, len(self.policy.ipcache))
        self.assertEqual(0, self.policy.request_number)
        
        # test new ips only
        iplist = ['209.34.91.45', '209.34.91.44', '209.34.91.47', '81.19.23.42']
        rated = self.policy.getRankedPeers(iplist)
        #print rated
        self.assertEqual(4, len(self.policy.ipcache), len(self.policy.ipcache))
        self.assertEqual(1, self.policy.request_number)
        
        # test one old, one new ip
        iplist2 = ['209.34.91.45', '81.19.23.100']# one old, one new
        rated = self.policy.getRankedPeers(iplist2) 
        self.assertEqual(5, len(self.policy.ipcache), len(self.policy.ipcache))
        self.assertEqual(2, self.policy.request_number)
        
        # now test only cached ips
        ['209.34.91.45', '209.34.91.44', '209.34.91.47'] # only old
        rated = self.policy.getRankedPeers(iplist2) 
        self.assertEqual(5, len(self.policy.ipcache), len(self.policy.ipcache))
        self.assertEqual(2, self.policy.request_number) # no new request
    
if __name__ == '__main__':
    print "Usage: 'python %s <SIS-address>' with SIS-address having the form: 127.0.0.1:8080" % sys.argv[0]
    if len(sys.argv)>1:
	SIS_URL="http://%s/sis/ClientEndpoint?wsdl" % sys.argv[1]
    print "use sis url", SIS_URL
    logging.basicConfig(level=logging.INFO)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSISRanking)
    unittest.TextTestRunner(verbosity=2).run(suite)
