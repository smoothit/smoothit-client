from threading import Thread

import logging
import time

def start_torrent_selection(cache_instance, selector, selection_interval=None, max_torrents = 5, stay_in_torrents=4):
    ''' Creates a new TorrentSelection instance of the type specified in the config.    selection interval is in seconds.
    '''
    
    ts = TorrentSelection(cache_instance, selector, selection_interval, max_torrents = max_torrents, stay_in_torrents = stay_in_torrents)
    ts.start()
    return ts

class TorrentSelection(Thread):
    ''' The TorrentSelection class obtains torrents from an external
        source in regular intervals and calls the join_swarm method of the
        cache.
    '''
    
    stopped = False
    
    def __init__(self, cache_instance, selector, selection_interval = None, max_torrents = 5, stay_in_torrents=4):
        Thread.__init__(self)
        self.cache = cache_instance
        
        self._logger = logging.getLogger("Cache.TorrentSelection")
        
        assert selector
        self.selector = selector 
        
        assert selection_interval
        self.selection_interval = selection_interval
        # or self.cache_config.get_value('torrent_selection_interval')
        
        assert max_torrents    
        self.max_torrents = max_torrents
        # or self.cache_config.get_value('max_torrents')
            
        self.stay_in_torrents = stay_in_torrents
        # or self.cache_config.get_value('stay_in_torrents')
        
    def run(self):
        while not self.stopped:
            joined = self.get_torrents()
            self._logger.info("Joined %d new torrents" % joined)
            #print "joined %d " % joined
            time.sleep(2)
            self.cache.update_download_settings()
            time.sleep(self.selection_interval)   
    
    def stop(self):
        self.stopped = True

    def get_torrents(self):
        ''' Obtains torrent files and the corresponding swarm informations from
            the installed selector.
            Returns the number of newly added torrents!
        '''
        torrent_stats = self.selector.retrieve_torrent_stats(self.max_torrents)
        assert len(torrent_stats) <= self.max_torrents, "max=%d but got %s" % (self.max_torrents, torrent_stats) 

        if len(torrent_stats) == 0:
            self._logger.warn("getTorrentStats returned no new torrents.")
#        else:
            #Algorithm:
            # fetch new max_torrents
            # analyze active torrents: keep best stay_in_torrents, fill up with best rated new torrents
            
            # free up some slots
            #rated_active = self.cache.get_up_rated_downloads()
            #to_leave = rated_active[self.stay_in_torrents :]
            #to_stay = rated_active[0:self.stay_in_torrents]
            
            #for id in to_leave:
            #    self.cache.leave_swarm(id)
            #fill_up = self.max_torrents-len(to_stay)
            #self._logger.info("Leave torrents %d, stay in %d, add new %d" % (len(to_leave), len(to_stay), fill_up))
            
            #strip running downloads from the candidate list
            #candidates = [(t_id, t_url) for (t_id, t_url, t_rate) in torrent_stats if not self.cache.is_running(t_id)]

            #TODO: should apply this for all running downloads!!!
            #self.start_connections(t_id)
            
            #to_join = candidates[0:fill_up]
        self._logger.info("found torrents: %d" % len(torrent_stats))    
        self._logger.info("torrent stats: %s" % torrent_stats)        
        old_torrents = self.cache.get_active_downloads_ids()
        self._logger.info("old torrents: %s" % old_torrents)
            
        new_torrents = [id for (id, url, rate) in torrent_stats if id not in old_torrents]
            
        self._logger.info("Got torrent ids : %s", new_torrents)
            
        nr = self.cache.max_downloads - min(len(old_torrents), self.stay_in_torrents)
        self._logger.info("Will join torrents %d" % nr)
        new_torrents = new_torrents[0:nr]
        self._logger.info("Selected new torrents: %s" % new_torrents)
        self._logger.info("Connections for old torrents: %s" % old_torrents)
            
        for t_id in new_torrents: 
                #to_join: #TODO: use rating for new downloads!
                #if self.processTorrent(t_id, t_url, t_rate):
                #TODO: process rating! pass it to cache repl. policy???
            self._logger.debug("add torrent: %s" % t_id)
            assert not self.cache.is_running(t_id)
                    
            tdef = self.selector.load_torrent_by_id(t_id)
            self.cache.join_swarm(tdef, t_id)
                
        for t_id in self.cache.get_active_downloads_ids():
            self._logger.debug("starting connections for torrent: %s" % t_id)
            self.start_connections(t_id)

        return len(new_torrents)
    
    def start_connections(self, torrent_hash):
        ''' Starts the connections that are specified in the peer list.
        '''
        peer_dict = self.getPeerDict(torrent_hash) 

        if len(peer_dict.keys()) > 0:
            self.cache.start_connections(torrent_hash, peer_dict)
        
    def getPeerDict(self, torrentID, with_seeds = True, max_peers = 20):
        ''' Obtains the a dictionary with peer recommendations for the specified torrent from the
            SIS.'''
        return self.selector.retrieve_local_peers_for_active_torrents([torrentID], max_peers, with_seeds)