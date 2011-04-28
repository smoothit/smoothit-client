from BaseLib.Core.simpledefs import *
from threading import Thread
from SisClient.Common.PeerConfiguration import ConfigurationException
import logging
import time
import sys

cache_config = None
cache = None

def getInstance(cache_instance, config):
    ''' Creates a new Ratemanager instance of the type specified
        in the config.
    '''
    
    global cache_config, cache
    cache_config = config
    cache = cache_instance
    
    #TODO: extract constants
    method = cache_config.get_rate_management()
    if method == 'equal':
        return ShareEqual()
    elif method == 'on_demand':
        rm = ShareOnDemand()
        rm.start()
        return rm
    elif method == 'swarm_size':
        return ShareBySwarmSize()
    else:
        raise ConfigurationException("Unsupported rate allocation method %s" % method)
            
class RateManager:
    '''  The Ratemanger sets the upload- and downloadlimits for all downloads.
    '''
    
    def __init__(self):
        self.speed_limit = {DOWNLOAD: None, UPLOAD: None}
        self.con_limit = None
        self._logger = logging.getLogger("Cache.RateManager")
    
    def set_dl_limit(self, limit):
        ''' Sets the global download limit (KB/s).
        '''
        self.speed_limit[DOWNLOAD] = limit
        self._logger.info("max_download set to %d " % limit)
    
    def set_ul_limit(self, limit):
        ''' Sets the global upload limit (KB/s).
        '''
        self.speed_limit[UPLOAD] = limit
        self._logger.info("max_upload set to %d " % limit)
    
    def set_connection_limit(self, limit):
        ''' Sets the global connection limit.
        '''
        self.con_limit = limit
        self._logger.info("max connections set to %d " % limit)
    
    def adjust_speeds(self,downloads):
        ''' Adjusts download-, upload- and connection limit for all downloads.
        '''
        if len(downloads) > 0:
            factor = 1.0/len(downloads)
            uploading = []
            downloading = []
            
            for (id, download) in downloads.items():
                download.set_max_conns_to_initiate(int(factor * self.con_limit))
                ds = download.network_get_state(None,True, True)
                status = ds.get_status()
                if not status == DLSTATUS_STOPPED:
                    uploading.append((download,ds))
                    if not status == DLSTATUS_SEEDING:
                        downloading.append((download, ds))
                    else:
                        download.set_max_speed(DOWNLOAD, 1)
        
            self.set_speed(UPLOAD, uploading)
            
            if len(downloading) > 0:
                self.set_speed(DOWNLOAD, downloading)
                
    def set_speed(self, dir, downloads):
        ''' Sets the download- or uploadlimit for all downloads. 
        '''
        pass
            
class ShareEqual(RateManager):
    ''' Shares the ratelimit equal between all downloads.
    '''
    
    def __init__(self):
        RateManager.__init__(self)
                    
    def set_speed(self, dir, downloads):
        if len(downloads)==0: return
        factor = 1.0/len(downloads)
        for (download, ds) in downloads:
            download.set_max_speed(dir, int(factor * self.speed_limit[dir]))
            

class ShareOnDemand(RateManager, Thread):
    ''' Shares unused transmission rates between the other downloads.
    '''
    
    def __init__(self):
        Thread.__init__(self)
        RateManager.__init__(self)
        
    def run(self):
        while True:
            time.sleep(cache_config.get_rate_interval())
            cache.update_download_settings()
    
    def set_speed(self,dir, downloads):  
        todo = []
        available = self.speed_limit[dir]
        self._logger.info("Available %s speed is %d " % (dir, available))
        for (download, ds) in downloads:
            cur_speed = max(1, ds.get_current_speed(dir))
            max_speed = download.get_max_speed(dir)
            
            if (cur_speed/max_speed) < 0.6:
                download.set_max_speed(dir, cur_speed)
                available -= cur_speed
            else:
                todo.append((download, ds))
                available -= max_speed
        
        if len(todo) > 0 and available > 0:   
            amount = (1.0/len(todo)) * available
            
            for (download, ds) in todo:
                new_speed = amount + ds.get_current_speed(dir)
                download.set_max_speed(dir, new_speed)
        elif available > 0:
            amount = (1.0/len(downloads)) * available
            
            for(download, ds) in downloads:
                new_speed = amount + ds.get_current_speed(dir)
                download.set_max_speed(dir, new_speed)
        
class ShareBySwarmSize(RateManager):
    ''' Shares the ratelimit according to the swarm size.
    '''
    
    def __init__(self):
        RateManager.__init__(self)
        
    def set_speed(self,dir, downloads):
        
        swarm_size_total = 0
        for (download, ds) in downloads:
            swarm_size_total += ds.get_num_peers()
        
        for (download, ds) in downloads:
            factor = float(ds.get_num_peers())/swarm_size_total
            download.set_max_speed(dir, int(factor * self.speed_limit[dir]))