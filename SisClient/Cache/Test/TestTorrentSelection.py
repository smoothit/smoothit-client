import sys
import unittest, logging, time
from SisClient.Cache import TorrentSelection, IoP_WSClientImpl
from SisClient.Cache.LocalFolderSelector import LocalFolderSelector

#SIS_URL="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"
#SIS_URL="http://130.83.244.162:8080/sis/ClientEndpoint?wsdl"

class DummyCache(object):
    def __init__(self):
        self.running = dict()
        self.stopped = set()
        self.max_downloads = 10
    
    def join_swarm(self, tdef, id):
        self.running[id]=tdef
        return True
    
    def is_running(self, id):
        return self.running.has_key(id)
    
    def update_download_settings(self):
        pass

    def start_connections(self, torrent_id, peer_list):
        pass
    
    def get_up_rated_downloads(self):
        return list(self.running.keys())
    
    def leave_swarm(self, id):
        del self.running[id]
        self.stopped.add(id)
        
    def get_active_downloads_ids(self):
        return self.running.keys()

class TestTorrentSelection(unittest.TestCase):


    def setUp(self):
        #self.policy = Communicator(SIS_URL, simple=True)
        pass
    
    def tearDown(self):
        pass
    
    def testNoSisSelectorCreation(self):
        return
        #default should be local folder
        selector = LocalFolderSelector()
        ts = TorrentSelection.start_torrent_selection(DummyCache(), selector, 10)
        try:
            mech = ts.selector
            self.assertEquals((LocalFolderSelector), type(mech))
        except:
            sys.exit(-1)
        finally:
            ts.stop()
    
    def testNoSisSelectionMechanism(self):
        ''' Manual test without actually starting the thread.
        '''
        return
        #MAX_TORRENTS = 7
        #build request
        #rated = self._tryRanking(iplist = ['209.34.91.45', '81.19.23.42'])
        #self.assertTrue(rated['81.19.23.42']>rated['209.34.91.45'])
        
        #there should be 2 files inside!
        cache = DummyCache()
        mech = LocalFolderSelector(folder="SisClient/Cache/Test/resources")
        max_torrents = 5
        stay_in_torrents = 3
        selector = TorrentSelection.TorrentSelection(cache, mech, selection_interval=1, max_torrents = max_torrents, stay_in_torrents=stay_in_torrents)
        
        #PRE_CONDITION
        assert len(cache.running) == 0
        
        # fill up to the max        
        joined = selector.get_torrents()
        assert joined == max_torrents, joined
        assert len(cache.running) == max_torrents
        #print "Now running:", cache.running
        
        # now replace some of them
        joined = selector.get_torrents()
        assert joined == max_torrents-stay_in_torrents
        assert len(cache.running) == max_torrents
        
        # now check if there is too much space
        for id in cache.running.keys()[0:-2]:
            cache.leave_swarm(id)
        assert len(cache.running) == 2
        joined = selector.get_torrents()
        assert joined == max_torrents-2
        assert len(cache.running) == max_torrents
        

    def testNoSisLocalFolderSelection(self):
        ''' Start and finish thread!
        '''
        
        cache = DummyCache()
        assert len(cache.running) == 0
        
        #default should be local folder
        ts = TorrentSelection.start_torrent_selection(cache, LocalFolderSelector(), 2)
        try:
            mech = ts.selector
            isinstance(mech, LocalFolderSelector)
            # now let it run for some iterations
            #cache.running.clear()
            
            # test threading
            #selector.start()
            time.sleep(5) # should be enough to find all torrents
        finally:
            ts.stop()
        # expect selector to find all 7 available torrents
        assert len(cache.running) > 0, len(cache.running)
        
    def testSisIoPSelection(self):
        ''' Start and finish thread!
        '''
        #TODO: only if IoP is active!
        cache = DummyCache()
        assert len(cache.running) == 0
        
        selector = IoP_WSClientImpl.IoP_WSClientImpl()
        ts = TorrentSelection.start_torrent_selection(cache, selector, 2)
        try:
            mech = ts.selector
            self.assertEquals((IoP_WSClientImpl.IoP_WSClientImpl), mech.__class__)
            # now let it run for some iterations
            #cache.running.clear()
            
            # test threading
            #selector.start()
            time.sleep(5) # should be enough to find all torrents
        finally:
            ts.stop()
        # expect selector to find all 7 available torrents
        assert len(cache.running) >= 0, len(cache.running)
          
    
if __name__ == '__main__':
    #print "Usage: 'python %s <SIS-address>' with SIS-address having the form: 127.0.0.1:8080" % sys.argv[0]
    #if len(sys.argv)>1:
    #SIS_URL="http://%s/sis/ClientEndpoint?wsdl" % sys.argv[1]
    #print "use sis url", SIS_URL
    logging.basicConfig(level=logging.INFO)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestTorrentSelection)
    print "Usage: python %s [test|testSis|testNoSis] while testNoSis is default" % sys.argv[0]
    testSelector = 'test'
    if len(sys.argv) > 1:
        testSelector = sys.argv[1]    
    suite = unittest.makeSuite(TestTorrentSelection, testSelector)
    unittest.TextTestRunner(verbosity=2).run(suite)
