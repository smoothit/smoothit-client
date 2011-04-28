from SisClient.Cache.Test.TestLocalFolder import TestLocalFolder
from SisClient.Cache.Test.TestTorrentSelection import TestTorrentSelection
from SisClient.Cache.Test.TestIoP_WSClient import TestIoP_WSClient
from SisClient.Test.test_config import TestConfig
from SisClient.TrackerExt.Test import TestSupporterMonitor
import unittest
import logging
import sys

from TestNeighborSelection import TestNeighborSelection
from TestOddEvenRanking import TestOddEvenRanking 
from TestSameHostRanking import TestSameHostRanking 
from TestBiasedUnchoking import TestBiasedUnchoking
from TestGeoIPRanking import TestGeoIPRanking
from TestSameIPPrefix import TestSameIPPrefixPolicy

if __name__ == "__main__":
    #logging.disable(logging.DEBUG)
    logging.basicConfig(level=logging.ERROR)
    
    suite = unittest.TestSuite((
                unittest.makeSuite(TestNeighborSelection, 'test'),
                unittest.makeSuite(TestOddEvenRanking, 'test'),
                unittest.makeSuite(TestSameHostRanking, 'test'),
                unittest.makeSuite(TestGeoIPRanking, 'test'),
                unittest.makeSuite(TestBiasedUnchoking, 'test'),
                unittest.makeSuite(TestSameIPPrefixPolicy, 'test'),
                #IoP related tests
                unittest.makeSuite(TestLocalFolder, 'test'),
                unittest.makeSuite(TestTorrentSelection, 'testNoSis'),
                unittest.makeSuite(TestConfig, "test_update"),
                #unittest.makeSuite(TestSupporterMonitor.TestMonitoredPeer, 'test'),
                #unittest.makeSuite(TestSupporterMonitor.TestMonitoredSupporter, 'test'),
                #unittest.makeSuite(TestSupporterMonitor.TestSupporterMonitor, 'test')
        ))
    if len(sys.argv) > 1 and "nosis" in sys.argv:
        #default tests are enough!
        print "Skipped all tests that require a running SIS instance!!!"
    else:
        # import some packets that otherwise are not required
        from TestMonitorReports import TestMonitorReports
        from TestSISRanking import TestSISRanking
        addon = unittest.TestSuite((
                unittest.makeSuite(TestMonitorReports, 'test'),
                unittest.makeSuite(TestSISRanking, 'test'),
                unittest.makeSuite(TestIoP_WSClient, 'test'),
                unittest.makeSuite(TestTorrentSelection, 'testSis'),
                unittest.makeSuite(TestConfig, "test_with_sis_update")
        ))
        suite.addTest(addon)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(len(result.errors) + len(result.failures))
    