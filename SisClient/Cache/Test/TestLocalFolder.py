from SisClient.Cache.LocalFolderSelector import LocalFolderSelector, get_torrents
import unittest, logging
from BaseLib.Core.API import TorrentDef
from SisClient.Utils.common_utils import get_id
#from SisClient.Cache.TorrentSelection import LocalFolder, SIS

#SIS_URL="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"
#SIS_URL="http://130.83.244.162:8080/sis/ClientEndpoint?wsdl"

TORRENT_FOLDER = "SisClient/Cache/Test/resources"

class TestLocalFolder(unittest.TestCase):


    def setUp(self):
        #self.policy = Communicator(SIS_URL, simple=True)
        self.selector = LocalFolderSelector(folder=TORRENT_FOLDER)
    
    def tearDown(self):
        pass

    def testReadingTorrents(self):
        '''test reading torrent defs from torrent directory'''
        files = get_torrents(TORRENT_FOLDER)
        assert len(files)==7, files
        
    
    def testLocalFolder(self):
        #build request
        #rated = self._tryRanking(iplist = ['209.34.91.45', '81.19.23.42'])
        #self.assertTrue(rated['81.19.23.42']>rated['209.34.91.45'])
        
        # dummy test
        self.selector.report_activity("foo", "bar", None)
        
        # test limited number
        torrents = self.selector.retrieve_torrent_stats(5)
        assert len(torrents) == 5, "torrents are %s" % torrents
        
        # test all
        torrents = self.selector.retrieve_torrent_stats(1000)
        assert len(torrents) == 7
        ids = []
#        print "torrents are: ", torrents
        for (id, url, rate) in torrents:
            tdef = TorrentDef.load(url)
            assert get_id(tdef) == id
            #print "%s with rating %s" % (tdef.get_name(), rate)
            assert rate == 100
            ids.append(id)
            
        # test local peers
        peers = self.selector.retrieve_local_peers_for_active_torrents(ids, 100, True)
        assert len(peers) == 0
        
        # dummy test for config parameters
        params = self.selector.retrieve_configuration_parameters("localhost")
        assert len(params) == 0
    
    def testRetrieveLocalPeersForActiveTorrents(self):
        # without torrents
        torrent_dict = self.selector.retrieve_local_peers_for_active_torrents(list_of_torrent_ids=[],
                                                                   maximum_number_of_peers=10,
                                                                   include_seeds=False)
        assert len(torrent_dict) == 0
        # now with torrents
        
            
if __name__ == '__main__':
    #print "Usage: 'python %s <SIS-address>' with SIS-address having the form: 127.0.0.1:8080" % sys.argv[0]
    #if len(sys.argv)>1:
    #SIS_URL="http://%s/sis/ClientEndpoint?wsdl" % sys.argv[1]
    #print "use sis url", SIS_URL
    logging.basicConfig(level=logging.INFO)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalFolder)
    unittest.TextTestRunner(verbosity=2).run(suite)
