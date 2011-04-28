from BaseLib.Core import simpledefs
from BaseLib.Core.simpledefs import UPLOAD
from SisClient.Common import constants
from SisClient.Cache.CacheConfiguration import ConfigurationException
import logging
import time
#from traceback import *

cache = None

def getInstance(cache_instance, policy_name):
    ''' Creates a new ReplacementStrategy instance of the type specified
        in the config.
    '''
    
    global cache, cache_config
    
    cache = cache_instance

    if policy_name == constants.RP_FIFO:
        return FIFO()
    elif policy_name == constants.RP_SMALLEST_SWARM:
        return SmallestSwarm()
    elif policy_name == constants.RP_UNVIABLE:
        return Unviable()
    elif policy_name == constants.RP_SLOWEST_SWARM:
        return SlowestSwarm()
    else:
        raise ConfigurationException("Unsupported policy: %s" % policy_name)
        

class ReplacementStrategy:
    ''' The ReplacementStrategy manages the local disc space and the download slots.
    '''
    
    def __init__(self):
        self._logger = logging.getLogger("Cache.ReplacementPolicy")
        
    def free_up_disc_space(self, size):
        ''' Tries to free up enough disc space for a new download. If it is not
            possible to free up enough disc space false is returned.
        '''
        while size > cache.available_disc_space:
            try:
                last = len(cache.stopped_downloads) - 1
                (id, dl) = cache.stopped_downloads[last]
                cache.leave_swarm(id, delete=True)
            except:
                return False
        return True
    
    def get_download_slot(self):
        ''' Tries to get a download slot for a new download.
            Returns False if no download slot is available.
        '''
        (id, dl) = self.select_download()
        self._logger.info("Replace download: %s" % id)
        if not id == None:
            cache.leave_swarm(id)
            return True
        else:
            return False
    
    def select_download(self):
        ''' Selects the download that should be stopped to free a download slot. 
        '''
        pass
    
    
class FIFO(ReplacementStrategy):
    ''' Replaces the oldest download.
    '''
    
    def __init__(self):
        ReplacementStrategy.__init__(self)
        self._logger.warn("Use FIFO Replacement strategy")
    
    def select_download(self):
        try:
            return cache.active_downloads[0]
        except:
            return (None, None)
    
class SmallestSwarm(ReplacementStrategy):
    ''' Replaces the download with the smallest swarm.
    '''
    
    def __init__(self):
        ReplacementStrategy.__init__(self)
    
    def select_download(self):
        result = (None, None)
        swarmSize = None
        time.sleep(5)
        for (id, dl) in cache.active_downloads.items():
            ds = dl.network_get_state(None,True, True)
            numPeers = ds.get_num_peers()
            if swarmSize == None or swarmSize > numPeers:
                swarmSize = numPeers
                result = (id, dl)
            
        return result

class SlowestSwarm(ReplacementStrategy):
    ''' Replaces the download with the lowest upload speed.
    '''
    
    def __init__(self):
        ReplacementStrategy.__init__(self)
        self._logger.warn("Use Slowest Swarm Replacement strategy")
    
    def select_download(self):
        result = (None, None)

        downloads = cache.active_downloads
        if len(downloads) > 0:
            time.sleep(5)#TODO: why sleep???
            min_upload = -1
            for (id, dl) in downloads.items():
                ds = dl.network_get_state(None,False, True) # don't return peer list but return the state back 
                upload = ds.get_current_speed(UPLOAD)
                if upload > min_upload:
                    min_upload = upload
                    result = (id, dl)                
        
        return result
    

class Unviable(ReplacementStrategy):
    ''' Checks if a active download is unviable and replaces it with a
        stopped download.
    '''
    
    def __init__(self):
        ReplacementStrategy.__init__(self)
        cache.session.set_download_states_callback(self.states_callback, True)
    
    def states_callback(self, dslist):
        for ds in dslist:
            if not ds.get_status() == simpledefs.DLSTATUS_STOPPED:
                numPeers = ds.get_num_peers()
                dl = ds.get_download()
                max_speed = dl.get_max_speed('up')
                cur_speed = ds.get_current_speed('up')
                if len(cache.stopped_downloads) == 0:
                    break
                
                if (numPeers < cache_config.get_min_leechers()
                    and (cur_speed/max_speed) < cache_config.get_min_ulfactor()):
                    
                    for (id, download) in cache.active_downloads:
                        if dl == download:
                            cache.leave_swarm(id)
                            break
                        
                    (id, download) = cache.stopped_downloads.pop(0)
                    cache.restart_download(id, download)

        
        return (20.0, True)
            
    
    def select_download(self):
        return (None, None)
                
                
            
        