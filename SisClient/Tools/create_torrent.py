import sys, os
from BaseLib.Core.TorrentDef import TorrentDef
from SisClient.Testbed.Utils.utils import FileUtils
from SisClient.Common import constants
from SisClient.Tools.add_playtime import videostats_via_ffmpeg

def create_torrent(file, port, try_vod = True):
    '''
    Creates a torrent for the given file. Returns a string representing the
    path to the torrent file.
    If try_vod is True try to add the playtime to the torrent making it "streamable".
    '''
    
    # generate torrent    
    tdef = TorrentDef()
    url = "http://localhost:%s/announce/" % port
    tdef.set_tracker(url)
    #tdef.set_create_merkle_torrent(True)
    #tdef.set_piece_length(self._pieceSize)
    
    if try_vod:
        torrent_name = FileUtils.get_relative_filename(file) + constants.TORRENT_VOD_EXT
        # set playtime
        playtime = videostats_via_ffmpeg(file)['playtime']
        print "playtime", playtime
    else:
        torrent_name = FileUtils.get_relative_filename(file) + constants.TORRENT_DOWNLOAD_EXT
        playtime = None
        print "Create a non-streamable torrent"
            
    tdef.add_content(file, playtime=playtime)
    tdef.finalize()
    
    torrent_dir = os.getcwd()
    torrent = os.path.join(torrent_dir, torrent_name)
    tdef.save(torrent)
    
    print "created torrent file: %s" % torrent
    print "Tracker uses the announce URL: %s" % tdef.get_tracker()

    return tdef
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "GOT: %s" % sys.argv
        print "Usage: %s <content_file> <tracker_port> [vod]" % sys.argv[0]
        sys.exit(-1)
    file = sys.argv[1]
    port = sys.argv[2] 
    if len(sys.argv) >3 and sys.argv[3]=="vod":
        vod = True
    else:
        vod = False
    create_torrent(file, port, vod)