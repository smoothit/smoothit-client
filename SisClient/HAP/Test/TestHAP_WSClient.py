import logging
import unittest

from SisClient.HAP.HAPInterface import HAP_WSClient
from SisClient.HAP.HAPInterface import HAPNeighbourStatisticsDTO

class TestHAP_WSClient(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def tearDown(self):
        pass
    
    def testReportActivity(self):
        self._client = HAP_WSClient("http://localhost:8080/sis/HAPEndpoint",
                                    "127.0.0.1", 5577)
        n1 = HAPNeighbourStatisticsDTO(1024, "192.168.0.75", 1024)
        n2 = HAPNeighbourStatisticsDTO(2048, "192.168.0.83", 2048)
        
        nstats = [n1, n2]
        
        self._client.report_activity(nstats)
        self._client = None
        
    def testOwnIPCanBeNone(self):
        self._client = HAP_WSClient("http://localhost:8080/sis/HAPEndpoint",
                                    None, 5588)
        n1 = HAPNeighbourStatisticsDTO(1024, "192.168.0.75", 1024)
        n2 = HAPNeighbourStatisticsDTO(2048, "192.168.0.83", 2048)
        
        nstats = [n1, n2]
        
        self._client.report_activity(nstats)
        self._client = None
            
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHAP_WSClient)
    unittest.TextTestRunner(verbosity=2).run(suite)