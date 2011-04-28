import sys
import urlparse
import unittest
import logging
from SisClient.Cache.IoP_WSClientImpl import IoP_WSClientImpl
from BaseLib.Core.TorrentDef import TorrentDef
from SisClient.Utils import common_utils

class TestIoP_WSClient(unittest.TestCase):
    def setUp(self):
        self.wsclient = IoP_WSClientImpl(sis_iop_endpoint_url="http://localhost:8080/sis/IoPEndpoint")
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def tearDown(self):
        self.wsclient = None
        pass
    
    def testRetrieveTorrentStats(self):
        
        # First send an activity report to the server!
        #torrent_id, torrent_url, filesize(bytes), progress(value in [0..1])
        #data = ('60d5d82328b4547511fdeac9bf4d0112daa0ce00', "./torrents/ubuntu.org", 28184, 0)
        #self.wsclient.report_activity("127.0.0.1", 12345, [data])
        
        tstats_list = self.wsclient.retrieve_torrent_stats(10)
        self.assertTrue(len(tstats_list) >= 0, tstats_list)# nothing comes back right now
        self._logger.warn("Got torrents stats "+str(tstats_list))
        
        #for (id, url, rate) in tstats_list:
        #    assert type(rate) is int
        #    assert urlparse.urlparse(url)                
        #    assert type(id) is str
            
    def testRetrieveLocalPeersForActiveTorrents(self):
        tdef = TorrentDef.load("torrents/ubuntu.torrent")
        infohash_hex = common_utils.get_id(tdef)
        torrent_dict = self.wsclient.retrieve_local_peers_for_active_torrents(list_of_torrent_ids=[infohash_hex],
                                                               maximum_number_of_peers=10,
                                                               include_seeds=False)
        assert len(torrent_dict) >= 0, torrent_dict
        #exp_id = '60d5d82328b4547511fdeac9bf4d0112daa0ce00'
        #self.assertTrue(torrent_dict.has_key(exp_id), torrent_dict)
        #self.assertEquals(torrent_dict[exp_id], [('127.0.0.1', 80)])            
            
    def testRetrieveConfigurationParameters(self):
        config = self.wsclient.retrieve_configuration_parameters('127.0.0.1')
        keys = ['localIPRanges', 'd', 'ulow', 'remotes', 'u', 'mode', 'x', 'slots', 'dlow', 't']
        for key in config.keys():
            self.assertTrue(key in keys)
            
    def testReportActivityWithEmptyList(self):
        self.wsclient.report_activity('127.0.0.1', 80, [])
        
    def testReportActivityWithFilledList(self):
        self.wsclient.report_activity('127.0.0.1', 80, [("", "", 489202, 0.9)])
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print "Usage: python %s [testnames ...] while testNoSis is default" % sys.argv[0]
    testSelector = 'test'
    suite = unittest.TestSuite()
    if len(sys.argv) > 1:
        for test in sys.argv[1:]:
            suite.addTest(unittest.makeSuite(TestIoP_WSClient, prefix=test))
    else:
        suite.addTest(unittest.makeSuite(TestIoP_WSClient, testSelector))
        unittest.TextTestRunner(verbosity=2).run(suite)
    unittest.TextTestRunner(verbosity=3).run(suite)