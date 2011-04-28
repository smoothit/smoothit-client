import unittest

from BaseLib.Core.TorrentDef import TorrentDef
from SisClient.Utils.common_utils import has_torrent_video_files

class CommonUtilsTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_tdef_has_video_files_expected_true(self):
        try:
            tdef = TorrentDef.load("torrents/Locality-Demo.mp4.tstream")
            self.assertTrue(has_torrent_video_files(tdef))
        except:
            self.fail("There was some error while loading the torrent file.")
            
    def test_tdef_has_video_files_expected_false(self):
        try:
            tdef = TorrentDef.load("torrents/ubuntu.torrent")
            self.assertFalse(has_torrent_video_files(tdef))
        except:
            self.fail("There was an error while loading the torrent files.")
        
if __name__ == "__main__":
    unittest.main()