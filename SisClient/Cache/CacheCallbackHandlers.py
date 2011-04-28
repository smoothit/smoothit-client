from SisClient.Common.PeerCallbackInterface import PeerCallbackInterface
from BaseLib.Core.simpledefs import DLSTATUS_SEEDING

import logging

logger = logging.getLogger("Cache.Callback")

def default_became_seeder_callback(torrent_name):
    global logger
    logger.info("Cache became seeder for download %s" % torrent_name)

class CacheActiveDownloadTracker(PeerCallbackInterface):
    def __init__(self, callback_on_dl_done=default_became_seeder_callback):
        self._callback_on_dl_done = callback_on_dl_done
        
    def state_callback(self, ds):
        d = ds.get_download()
        torrent = d.get_def().get_name_as_unicode()
        status = ds.get_status()
        
        if status == DLSTATUS_SEEDING:
            self._callback_on_dl_done(torrent)
    
    def video_event_callback(self, d, event, params):
        # not implemented
        pass