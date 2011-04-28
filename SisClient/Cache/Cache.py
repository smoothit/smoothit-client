from BaseLib.Core import API, simpledefs
from SisClient.Cache.CacheConfiguration import CacheConfiguration
from SisClient.Cache import LocalFolderSelector
from SisClient.Cache.IoP_WSClientImpl import IoP_WSClientImpl
from SisClient.PeerSelection import NeighborSelection
from SisClient.RankingPolicy import RankingPolicy
from SisClient.Cache.CacheCallbackHandlers import CacheActiveDownloadTracker
from SisClient.Common.PeerCallbackHandlers import PeerCallbackHandlers
from SisClient.Common.CommonPeerHandlers import PeerActivityReportEmitter, PeerHTTPReporter, \
                                                PeerLocalReporter, PeerReporter
from SisClient.Testbed.Utils import utils as Testbed_utils
from threading import RLock
from SisClient.Common.PeerConfiguration import ConfigurationException
import CacheConsole
import Ratemanager
import ReplacementStrategy
import TorrentSelection
#import logging
import logging.config
import os
import socket
import sys
import time
import traceback

from SisClient.Utils import net_utils, common_utils

local_reporter = None

class Cache:
    ''' This class is used to start the cache applictaion.
    '''
    
    def __init__(self, cache_config):
        self._cache_config = cache_config
        self.active_downloads = {}
        self.stopped_downloads = {}
        self.save_dir = cache_config.get_directory()
        self.disc_space = cache_config.get_space_limit() * 1024 * 1024
        self.available_disc_space = self.disc_space
        self.dl_lock = RLock()
        
        self._logger = None
        self.ranking = None
        self.filtering = None
        self.replacement_strategy = None
        self.ratemanager = None
        self.handlers = None
        
        self._init_logger()
        self._init_cache_console()
        self._init_before_session()
        self.start_session(self._cache_config.get_port())
        self._init_after_session()
        self._init_callback_handler()
        self._init_selector()
        
    def _get_name(self):
        return "%s.%i" % (self.__class__.__name__, self._cache_config.get_id())
        
    def _init_logger(self):
        self._logger = logging.getLogger(self._get_name())
        
        self._logger.info("Initialized logger")
        global logger
        logger = self._logger
        
         
    def _init_cache_console(self):
        if self._cache_config.has_cache_console():
            CacheConsole.start_cache_console(self)
        
    def _init_before_session(self):
        self.ranking = RankingPolicy.selectRankingSource(self._cache_config.get_ranking_source(),
                                                    conf=self._cache_config)
        self._logger.warning("Ranking source is %s" % self.ranking)
        
        exclude_below = 1# allow only non-remote connections!
        self.filtering = NeighborSelection.createMechanism(self._cache_config.get_ns_mode(),
                                                            self.ranking,
                                                            exclude_below=exclude_below,
                                                            locality_pref=self._cache_config.get_locality_preference())
        self._logger.warning("Neighbor selection is %s" % self.filtering)
        self.max_downloads = self._cache_config.get_max_downloads()
        
    def _init_after_session(self):
        policy_name = self._cache_config.get_replacement_strategy()
        self.replacement_strategy = ReplacementStrategy.getInstance(self, policy_name)
        self.ratemanager = Ratemanager.getInstance(self, self._cache_config)
        self.ratemanager.set_dl_limit(self._cache_config.get_download_limit())
        self.ratemanager.set_ul_limit(self._cache_config.get_upload_limit())
        self.ratemanager.set_connection_limit(self._cache_config.get_connection_limit())
        
    def _init_callback_handler(self):
        self.handlers = PeerCallbackHandlers(self._get_name(),
                                               self._cache_config.get_report_interval())
        self.handlers.register_handler(PeerReporter(self._get_name()))
        self.handlers.register_handler(CacheActiveDownloadTracker())
        
        if self._cache_config.get_sis_url() is not None:
            ip_addr = net_utils.get_own_ip_addr()
            iop_url = self._cache_config.get_sis_iop_url()
            self.handlers.register_handler(PeerActivityReportEmitter(
                    (ip_addr, self._cache_config.get_port()),
                    self._cache_config.get_report_interval(),
                    sis_iop_endpoint_url=iop_url))
        
        if self._cache_config.get_report_to() is not None:
            if self._cache_config.get_report_to() == 'local_report':
                global local_reporter
                local_reporter = PeerLocalReporter(self._get_name(), self._cache_config.get_id(),
                                               self.session, self._cache_config.get_directory())
                self.handlers.register_handler(local_reporter)
            else:
                self.handlers.register_handler(PeerHTTPReporter(self._get_name(),
                                                                  self._cache_config.get_id(),
                                                                  self._cache_config.get_report_to(),
                                                                  self.sconfig,
                                                                  self._cache_config.get_compress_xml_reports(),
                                                                  self._cache_config.get_serialization_method(),
                                                                  is_iop=True))
                
    def _init_selector(self):
        selector = None
        mode = self._cache_config.get_torrent_selection_mechanism()
        if mode == 'local_folder':
            selector = LocalFolderSelector.LocalFolderSelector(self._cache_config.get_torrent_directory())
            self._logger.info("Run in local folder mode")
        elif mode == 'SIS':
            #selector = self._cache_config.get_ws_client() 
            selector = IoP_WSClientImpl(self._cache_config.get_sis_iop_url())
            selector.set_torrent_dir(self._cache_config.get_torrent_directory())
            #FIXME: we now create these instances twice!!! once in cache config and then here! Should rather use a wrapper here!
            self._logger.info("Run in WS torrent selection mode")
        else:
            raise ConfigurationException("Unsupported torrent selection mechanism!"+str())
                                         
        assert selector is not None
        self._logger.info("Use torrent selection method "+str(selector))
        
        interval = self._cache_config.get_torrent_selection_interval()
        max_torrents = self._cache_config.get_max_torrents()
        assert max_torrents >= self.max_downloads
        stay_in_torrents = self._cache_config.get_stay_in_torrents()
        self.torrent_selection = TorrentSelection.start_torrent_selection(
                                    self, selector,
                                    selection_interval=interval,
                                    max_torrents=max_torrents, stay_in_torrents=stay_in_torrents)


        
    def start_session(self, port):
        ''' Sets the values of the SessionStartupConfig an creates
            a new session.
        '''
        
        self.sconfig = API.SessionStartupConfig()
        self.sconfig.set_state_dir(self._cache_config.get_directory())    
        self.sconfig.set_listen_port(port)    
        self.sconfig.set_overlay(False)
        self.sconfig.set_megacache(False)
        self.sconfig.set_upnp_mode(simpledefs.UPNPMODE_DISABLED)
        self.session = API.Session(self.sconfig)
        global session
        session = self.session
                   
    def join_swarm(self, tdef, id):
        ''' Starts a new download with the given torrent definition. This method
            tries to allocate disc space and to get a download slot before the
            new download can be started. If the cache already contains the 
            specified download and it is stopped, this method can be used to
            restart the download. The id is used to identify the download.
        '''
        self.dl_lock.acquire()
        try:
            dl = self.get_download(id, stopped=True, pop=True)
            if not dl == None:
                if self.get_download_slot():
                    self.restart_download(id, dl)
                return True
            length = tdef.get_length(tdef.get_files())
            if self.allocate_disc_space(length):
                try:
                    dlcfg = self.get_startup_config()
                    dl = self.session.start_download(tdef, dlcfg)
                    self._logger.info("Join new swarm %s" % dl.get_def().get_name())
                    dl.set_state_callback(self.handlers.state_callback, getpeerlist=True)
                    if self.get_download_slot():
                        self.active_downloads[id] = dl
                    else:
                        time.sleep(5)
                        dl.stop()
                        self.stopped_downloads[id]=dl
                    return True
                except:
                    self.available_disc_space += length
                    self._logger.warn("Failed to start download: "+tdef.get_name(), exc_info=True)
                    return False 
            else:
                self._logger.warn("Failed to allocate disc space for "+tdef.get_name())
                return False
        except :
            self._logger.warn("Failed to join swarm "+tdef.get_name(), exc_info=True)
            return False
        finally:
            #print >> sys.stderr,"After join: active %s and stopped %s" % (self.active_downloads, self.stopped_downloads)
            self.dl_lock.release()

    def print_active(self):
        list = []
        for dl in self.active_downloads.values():
            list.append(dl.get_def().get_name())
        self._logger.error("active: %s" % list)
    
    def leave_swarm(self, id, delete=False): 
        ''' This method stops a currently running download.
            In addition the files of a running or stopped download can be deleted.
        '''
        assert id in self.active_downloads.keys() , id
        
        self.dl_lock.acquire()
        try:
            if delete:
                dl = self.get_download(id, stopped=True, pop=True)
                length = dl.get_def().get_length(dl.get_def().get_files())
                self.available_disc_space += length
            else:
                dl = self.get_download(id, pop=True)
                self._logger.info("Leave swarm %s" % dl.get_def().get_name())
                self.stopped_downloads[id] = dl
            dl.stop_remove(delete, delete)
            return True
        except:
            traceback.print_exc()
            return False
        finally:
            self.dl_lock.release()
            
    def restart_download(self, id, dl):
        ''' Restarts a stopped download.
        ''' 
        self._logger.info("Re-join swarm %s" % dl.get_def().get_name())
        dl.set_max_speed(simpledefs.DOWNLOAD, 1)#TODO: reuse config!!!
        dl.set_max_speed(simpledefs.UPLOAD, 1)
        dl.restart()
        dl.set_state_callback(self.handlers.state_callback, getpeerlist=True)
        self.active_downloads[id] = dl
        time.sleep(3)
        self.update_download_settings()
        
    def get_download_slot(self):
        ''' This method checks if a download slot is available.
            If no download slot is available the replacement strategy is
            used to stop a running download.
        '''
        if len(self.active_downloads) < self.max_downloads:
            return True
        else:
            return self.replacement_strategy.get_download_slot()
    
    def get_startup_config(self):
        ''' Sets values of the DownloadStartupConfig.
        '''
        
        dlcfg = API.DownloadStartupConfig()
        dlcfg.set_dest_dir(self.save_dir)
        dlcfg.set_max_speed(simpledefs.DOWNLOAD, 1)
        dlcfg.set_max_speed(simpledefs.UPLOAD, 1)
        dlcfg.set_max_uploads(self._cache_config.get_max_upload_slots_per_download())
        min_uploads = min(dlcfg.get_min_uploads(), self._cache_config.get_max_upload_slots_per_download())
        dlcfg.set_min_uploads(min_uploads)
        
        return dlcfg
    
    def get_download(self, id, stopped=False, pop=False):
        ''' Returns the download specified by the id.
        '''
        
        #print >> sys.stderr, "Check torrent: "+id
        #print >> sys.stderr, "Stopped: ", self.stopped_downloads
        #print >> sys.stderr, "Active: ", self.active_downloads
        if stopped:
            downloads = self.stopped_downloads
        else:
            downloads = self.active_downloads
            
        for (dl_id, dl) in downloads.items():
            if dl_id == id:
                if pop:
                    del downloads[dl_id]
                return dl 
        return None
        
    def is_running(self, id):
        ''' Returns if the download specified by the id is currently running.
        '''
        return self.active_downloads.has_key(id)
        #return not(self.get_download(id) == None)
    
    def is_stopped(self, id):
        ''' Returns if the download specified by the id is currently stopped.
        '''
        
        return not(self.get_download(id, stopped=True) == None)
    
    def update_download_settings(self):
        ''' Updates the transmission rates of all running downloads.
        '''
        
        self.dl_lock.acquire()
        try:
            self.ratemanager.adjust_speeds(self.active_downloads)
        finally:
            self.dl_lock.release()
    
    def allocate_disc_space(self, file_size): 
        ''' Checks if enough disc space for the download is available
            and tries to free up the needed disc space.
        '''
        #print >> sys.stderr, "Available space: %d, required space: %d " % (self.available_disc_space, file_size)
        if file_size <= self.available_disc_space:
            self.available_disc_space -= file_size
            return True
         
        if self.replacement_strategy.free_up_disc_space(file_size):
            self.available_disc_space -= file_size
            return True
        
        return False
        
    def start_connections(self, id, peer_dict):
        ''' Starts new connections.
        '''
        
        # select active or passive download?
        assert id in self.active_downloads.keys() or id in self.stopped_downloads.keys()
        dl = self.active_downloads[id]
        #print>>sys.stderr, "download: %s session %s" % (dl, dl.sd)
        #TODO: acquire locks before starting connections?
        if dl.sd is None: # race condition? connect to them later! 
            return
        
        bt1dl = dl.sd.get_bt1download()
        stats = dl.sd.get_stats(False)
        
        if stats[0] != None:
            return
        
        for torrent_id, list_of_peers in peer_dict.items():
            for peer in list_of_peers:
                ip, port = peer
                try:
                    bt1dl.startConnection(ip, port, False) # False means -> immediate connection
                except:
                    self._logger.warn("Failed to connect to %s for torrent id %s" % (str(peer), str(torrent_id)), exc_info = True)
       
    def set_dl_limit(self, limit):
        ''' Sets the download limit of the cache and updates the rates
            for all running downloads.
        '''
        
        self.ratemanager.set_dl_limit(limit)
        self.update_download_settings()
        
    def set_ul_limit(self, limit):
        ''' Sets the download limit of the cache and updates the rates
            for all running downloads.
        '''
        
        self.ratemanager.set_ul_limit(limit)
        self.update_download_settings()
            
    def set_hostname(self):
        ''' This method is used to get the hostname of the cache,
            which is used by the cache_local mode of the NeighborSelection.
        '''
        
        own_ip = self.session.get_external_ip()
        hostname = socket.gethostbyaddr(own_ip)
        NeighborSelection.getInstance().set_cache_hostname(hostname)
        
    def get_status(self):
        ''' Returns the current status of the cache and its running downloads.
        '''
        return CacheStatus(self.active_downloads, self.stopped_downloads, self)

    def get_active_downloads_ids(self):
        ''' Return list of active torrent ids.
        '''
        return list(self.active_downloads.keys())

    def get_up_rated_downloads(self):
        ''' Return list of active torrent ids sorted by the descending upload rate.
        '''
        rated = [] # download id to rate!
        status = self.get_status()
        for ds in status.downloadstats:
            id = ds['id']
            rate = ds['up_rate']
            if id in self.active_downloads:
                rated.append( (rate, id) )
        return [id for (rate, id) in sorted(rated, reverse=True)]
    
    def run_forever(self):
        try:
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            on_exit()
        
class CacheStatus:
    
    def __init__(self, downloads, stopped, cache):
        self.dl = 0
        self.ul = 0
        self.active = len(downloads)
        self.stopped = len(stopped)
        self.downloadstats = []
        self.get_download_infos(downloads, stopped)
        self.cache = cache
    
    def get_download_infos(self, downloads, stopped):
        for (id, dl) in downloads.items():
            ds = dl.network_get_state(None,True, True)
            self.get_transfer_stats(dl)
            self.downloadstats.append({
                                  'id': id,
                                  'name': dl.get_def().get_name(),
                                  'progress': ds.get_progress() * 100,
                                  'down_rate': ds.get_current_speed('down'),
                                  'up_rate': ds.get_current_speed('up'),
                                  'seeds_peers': ds.get_num_seeds_peers()
                                  })
            
        for (id, dl) in downloads.items():
            self.get_transfer_stats(dl)
        
    def get_transfer_stats(self, dl):
        if dl.sd == None: return # TODO: race condition? sd = None means download is not running! 
        bt1dl = dl.sd.get_bt1download()    
        try:
            (up_total, down_total) = bt1dl.get_transfer_stats()
            self.dl += down_total/(1024*1024)
            self.ul += up_total/(1024*1024)
        except:
            pass
    
    def print_to_console(self):
        os.system('clear')
        
        max = self.cache.disc_space/1024/1024
        print >>sys.stderr, "Total disc space (MBs): %d" % max
        print >>sys.stderr, "Available disc space (MBs): %d" % (self.cache.available_disc_space/1024/1024)
        
        print >> sys.stderr, ("\nactive: %d stopped: %d downloaded: %d MB uploaded: %d MB\n" %  
                                (self.active, self.stopped, self.dl, self.ul))
        print >> sys.stderr, ('%2.2s %30.30s%10.10s%10.10s%10.10s%10.10s%10.10s' %
              ('#','name','progress','download','upload','peers','seeds'))
        for i in range(0,len(self.downloadstats)):
            ds = self.downloadstats[i]
            print >> sys.stderr, ('%2.0d %30.30s%9.1d%%%10.1f%10.1f%10s%10s' % 
                   (i+1,ds['name'],ds['progress'], ds['down_rate'], ds['up_rate'], 
                    ds['seeds_peers'][0], ds['seeds_peers'][1]))
        print >> sys.stderr,"\n"

def on_exit(signal=None, func=None):
    if not local_reporter == None:
        local_reporter.write_stats()
    logger.warn("Session shutdown")
    session.shutdown()
    logger.warn("wait some time") 
    time.sleep(1) # wait some time so session can stop gracefully
    logger.warn("sys exit (session shutdown takes too long?)")
    sys.exit()

#___________________________________________________________________________________________________
# MAIN
        
if __name__ == '__main__':
    LOG_FILE_NAME = "config/log_iop.conf"
    print "read logging config from file: ", LOG_FILE_NAME
    logging.config.fileConfig(LOG_FILE_NAME)
    
    cache_config = CacheConfiguration()
    cache_config.update_from_cl(sys.argv[1:])
    
    if cache_config.get_logfile() is not None:
        print >>sys.stderr, "Using logfile: %s" % cache_config.get_logfile()    
        common_utils.setup_cache_file_logger(cache_config.get_logfile())
       
    cache = Cache(cache_config)
    Testbed_utils.set_exit_handler(on_exit)
    cache.run_forever()