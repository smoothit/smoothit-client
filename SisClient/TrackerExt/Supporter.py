from SisClient.Common import constants
import optparse
import os
import sys
import tempfile
import time
import urllib

import SimpleXMLRPCServer

from BaseLib.Core.SessionConfig import SessionStartupConfig
from BaseLib.Core.Session import Session
from BaseLib.Core import simpledefs
from BaseLib.Core.TorrentDef import TorrentDef
from BaseLib.Core.DownloadConfig import DownloadStartupConfig

from SisClient.Testbed.Utils.utils import files_list

__author__ = "Markus Guenther"

class SupporterXMLRPCServer(object):
    def __init__(self, supporter):
        self._supporter = supporter # instance of SupporterServer (in order to notify it)
    
    def receive_peer_list(self, list_of_peer_tuples):
        # tuples adhere to the form (peer_id, ip, port)
        print >>sys.stdout, 'Received a list of peers to be unchoked...', list_of_peer_tuples
        self._supporter.push_supportee_list_to_choker(list_of_peer_tuples)
        return True
    
    def is_alive(self):
        '''This method can be called by an XMLRPC client in order to check whether the
        supporter is still alive and responding. If the supporter is not responding, the
        client will receive an exception, which he must catch and handle appropriately.
        
        @return:
            True, since the client only wants to see if the supporter is able to respond
        '''
        return True

class HTTPCommunicator(object):
    
    REGISTER_URI_TEMPLATE = "%sregister_supporter?id=%s&port=%i&min_peer=%i&max_peer=%i"
    
    def __init__(self, http_params):
        self._http_params = http_params
        
    def send_registration(self):
        try:
            urllib.urlopen(self.REGISTER_URI_TEMPLATE % (self._http_params['url'],
                                                     self._http_params['id'],
                                                     self._http_params['port'],
                                                     self._http_params['min_peer'],
                                                     self._http_params['max_peer']))
        except:
            print >>sys.stderr, "Unable to register at tracker (%s). Exiting." % self._http_params['url']
            sys.exit(1)

class SupporterServer(object):
    def __init__(self, options):
        self._directory = options.directory
        self._port = options.port
        self._torrent = options.torrent
        self._max_dl_rate = options.dlrate
        self._max_ul_rate = options.ulrate
        self._min_peer = options.min_peer
        self._max_peer = options.max_peer
        self._choke_objects = [] # list of all chokers...
        
    def init_session(self):
        scfg = SessionStartupConfig()
        scfg.set_state_dir(tempfile.mkdtemp())
        scfg.set_listen_port(self._port)
        scfg.set_overlay(False)
        scfg.set_megacache(False)
        scfg.set_upnp_mode(simpledefs.UPNPMODE_DISABLED)
        scfg.set_dialback(False)
        scfg.set_social_networking(False)
        scfg.set_buddycast(False)
        scfg.set_crawler(False)
        scfg.set_internal_tracker(False)
        
        self._session = Session(scfg)
        
    def start_torrents(self):
        torrents = []
        if os.path.isdir(self._torrent):
            # walk the dir and start all torrents in there
            torrents = files_list(self._torrent, [constants.TORRENT_DOWNLOAD_EXT, constants.TORRENT_VOD_EXT])
        else:
            torrents.append(self._torrent)
            
        for torrent in torrents:
            self.start_torrent(torrent)
        
    def start_torrent(self, torrent):
        tdef = TorrentDef.load(torrent)
        
        if not os.access(self._directory, os.F_OK):
            os.makedirs(self._directory)
        
        dscfg = DownloadStartupConfig()
        dscfg.set_dest_dir(self._directory)
        dscfg.set_video_events([simpledefs.VODEVENT_START,
                                simpledefs.VODEVENT_PAUSE,
                                simpledefs.VODEVENT_RESUME])
        dscfg.set_max_speed(simpledefs.DOWNLOAD, self._max_dl_rate)
        dscfg.set_max_speed(simpledefs.UPLOAD, self._max_ul_rate)
        dscfg.set_peer_type("S")
        #dscfg.set_video_event_callback(self.video_callback) # supporter should not play the files !
        
        d = self._session.start_download(tdef, dscfg)
        d.set_state_callback(self.state_callback)
        
        time.sleep(1) # give the download some time to fully initialize
        d.sd.dow.choker.set_supporter_server(True)
        
        
        self._tracker_url = tdef.get_tracker()[:tdef.get_tracker().find("announce")]
        self._id = d.sd.peerid
        self._choke_objects.append(d.sd.dow.choker)
        
    def init_communicator(self):
        self._communicator = HTTPCommunicator({'url' : self._tracker_url,
                                               'id' : self._id,
                                               'port' : self._port,
                                               'min_peer' : self._min_peer,
                                               'max_peer' : self._max_peer})
        self._communicator.send_registration()
        
    def run_forever(self):
        self.init_session()
        self.start_torrents()
        self.init_communicator()
        
        xmlrpc_server_handler = SupporterXMLRPCServer(self)
        xmlrpc_server = SimpleXMLRPCServer.SimpleXMLRPCServer(("0.0.0.0", self._port+1))
        xmlrpc_server.register_instance(xmlrpc_server_handler)
        xmlrpc_server.serve_forever()
        
    def state_callback(self, ds):
        return (0, False)
    
    def video_callback(self, d, event, params):
        pass
    
    def push_supportee_list_to_choker(self, supportee_list):
        for choker in self._choke_objects:
            choker.receive_supportee_list(supportee_list)
#___________________________________________________________________________________________________
# MAIN

if __name__ == "__main__":
    
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + " [options]")
    parser.add_option("-d", "--directory", dest="directory", default="supporter")
    parser.add_option("-p", "--port", type="int", dest="port", default=9000)
    parser.add_option("-t", "--torrent", dest="torrent", default=None)
    parser.add_option("-x", "--dlrate", type="int", dest="dlrate", default=1024)
    parser.add_option("-y", "--ulrate", type="int", dest="ulrate", default=4096)
    parser.add_option("-m", "--min_peer", type="int", dest="min_peer", default=1)
    parser.add_option("-n", "--max_peer", type="int", dest="max_peer", default=2)
    
    (options, args) = parser.parse_args()
        
    server = SupporterServer(options)
    server.run_forever()
