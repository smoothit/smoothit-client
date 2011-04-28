'''
Created on 07.12.2009

@author: pussep
'''
from BaseLib.Core.API import TorrentDef
from SisClient.Cache.IopApi import IopApi
from SisClient.Utils.common_utils import get_torrents
from SisClient.Common.PeerConfiguration import ConfigurationException
import logging
import os
import sys
import random

class LocalFolderSelector(IopApi):
    
    def __init__(self, folder = "./torrents"):
        IopApi.__init__(self) #
        self._logger = logging.getLogger("Cache.LocalFolder")
        self._load_torrents(folder)
        
    def _load_torrents(self, folder):
        self.folder = folder
        
        assert os.path.isdir(self.folder), "torrent dir %s must exist!" % self.folder  
        
        self.torrents = get_torrents(self.folder)
        self._logger.info("loaded torrents: %s" % self.torrents)
    
    def report_activity(self, ip_addr, port, downloads):
        '''downloads = list of tuples of the form ( torrent_id, torrent_url, filesize, progress )
        filesize in bytes
        progress in [0..1]
        '''
        pass # don't report anything
    
    def retrieve_torrent_stats(self, max_requested_torrents=10):
        '''return type is list of tuples of the form ( torrent_id, torrent_url, rate )
        '''
        ids = list(self.torrents.keys())
        random.shuffle(ids)
        def_rating = 100
        return [ (id, self.torrents[id][1], def_rating) for id in ids[0:max_requested_torrents]] 
    
    def retrieve_local_peers_for_active_torrents(self,
                                                 list_of_torrent_ids = [],
                                                 maximum_number_of_peers = 10,
                                                 include_seeds = False):
        '''return type is dict with torrent ids as keys and a list of 2-tuples of the form
        ( peer_ip_addr, peer_port )
        '''
        # TODO (mgu): Is this supposed to return an empty dict? (was an empty list before,
        # which was not compliant to the IopApi interface)
        return {}
    
    def retrieve_configuration_parameters(self, my_own_ip="127.0.0.1"):
        '''return type is dict, keys = parameter names (string), values = correct data types
        '''
        return dict()
    
    def load_torrent_by_path(self, t_url):
        ''' Helper method to let the selector decide whether we should load from disc or from web.
        '''
        tdef = TorrentDef.load(t_url) #TODO: could also du id-based! self.torrents[id]
        return tdef
    
    def load_torrent_by_id(self, id):
        ''' Helper method to let the selector decide whether we should load from disc or from web.
        '''
        if not self.torrents.has_key(id):
            print >>sys.stderr, self.torrents
            raise ConfigurationException("Unknown id %s" % id)
        return self.torrents[id][0]
