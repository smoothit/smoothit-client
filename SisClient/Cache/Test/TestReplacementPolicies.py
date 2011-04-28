from SisClient.Cache import ReplacementStrategy
from SisClient.Common import constants
import unittest, logging
from BaseLib.Core.API import TorrentDef
from SisClient.Utils.common_utils import get_torrents, get_id

TORRENT_FOLDER = "SisClient/Cache/Test/resources"

class TestReplacementPolicies(unittest.TestCase):

    
    def setUp(self):
        # map torrent id to (tdef, filename)
        torrents = get_torrents(TORRENT_FOLDER)
        self.downloads = []
         
        self.started_at = {}
        for (id, value) in torrents.items():
            (tdef, file) = value
            self.downloads.append(tdef)
            self.started_at[id] = 100-len(self.downloads)
            print "%s -> %s " % (id, tdef)
            
        print "\nStarted at: ", self.started_at
        self.assertEquals(7, len(self.downloads))
        self.assertEquals(7, len(self.started_at))
    
    def tearDown(self):
        pass
    
    def testFIFO(self):
        #policy = ReplacementStrategy.create_policy(None, constants.RP_FIFO)
        policy = ReplacementStrategy.FIFO(self.started_at)
        candidate_downloads = self.downloads

#        print "candidates=", candidate_downloads
        selected = policy.free_up_download_slots(0, candidate_downloads)
#        print "selected=", candidate_downloads
        self.assertEquals(0, len(selected))
     
        selected = policy.free_up_download_slots(1, candidate_downloads)
        self.assertEquals(1, len(selected))
        # start times are sorted in rverse oder of downloads!!!
        self.assertEquals(get_id(self.downloads[0]), get_id(selected[0]))
     
        max_torrents = len(self.downloads)
        # test max number  
        selected = policy.free_up_download_slots(max_torrents, candidate_downloads)
        self.assertEquals(max_torrents, len(selected))
        
        selected = policy.free_up_download_slots(max_torrents+1, candidate_downloads)
        self.assertEquals(max_torrents, len(selected))
        
        
        
if __name__ == '__main__':
    #print "Usage: 'python %s <SIS-address>' with SIS-address having the form: 127.0.0.1:8080" % sys.argv[0]
    logging.basicConfig(level=logging.INFO) #INFO) #DEBUG
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReplacementPolicies)
    unittest.TextTestRunner(verbosity=2).run(suite)
