import logging
import time

from traceback import print_exc
from BaseLib.Core import simpledefs
from SisClient.Common.PeerCallbackInterface import PeerCallbackInterface
from SisClient.Common import constants
from SisClient.Utils import common_utils

from SisClient.HAP.HAPInterface import HAP_WSClient
from SisClient.HAP.HAPInterface import HAPNeighbourStatisticsDTO

class ClientUptimeHandler(PeerCallbackInterface):
    '''Concrete callback implementation for the download state callback
    and the video event callback. The purpose of this handler class is to
    determine if a user-provided termination condition is fulfilled. If
    the condition is fulfilled, a graceful shutdown of the session thread
    will be initiated, followed by the triggering of a user-provided
    callback (see __init__), which can be used to inject cleanup code
    into the termination process.
    
    Attention: In general, this handler does only make sense if it used
    together with a leecher.
    '''
    
    _downloads = {}
    _logger = None
    _DEFAULT_BITRATE = 32768 * 3
    
    def __init__(self, session, method=constants.EXIT_ON_ALL_FINISHED, max_seeding_time=0,
                 callback=None):
        self._session = session
        self._method = method
        self._max_seeding_time = max_seeding_time
        self._logger = logging.getLogger("Client.UptimeHandler")
        self._callback = callback
    
    def state_callback(self, ds):
        '''This method will be called for every download that is currently
        active. Its sole purpose is to determine if the termination condition
        given by EXIT_ON_ALL_FINISHED or EXIT_ON_SEEDING_TIME is fulfilled.
        If the termination condition is neither of those two, the methods
        execution body will be skipped.
        
        Parameters:
            ds -- DownloadState object for a specific active download
            
        Return:
            NoneType
        '''
        if self._method == constants.EXIT_ON_PLAYBACK_DONE:
            return
        
        d = ds.get_download()
        torrent = d.get_def().get_name_as_unicode()
        status = ds.get_status()
        
        if self._downloads.has_key(torrent):
            # check if we have to perform an update; if so, store the
            # current time as well
            old_status, old_ts = self._downloads[torrent]
            if old_status != status:
                self._logger.debug("Client status update to %i" % status)                
                self._downloads[torrent] = (status, time.time())
        else:
            # new entry, so just place the status with the current
            # timestamp in the dict if it indicates a download
            if status == simpledefs.DLSTATUS_DOWNLOADING:
                self._downloads[torrent] = (status, time.time())
        
        shutdown = False
        if self._method == constants.EXIT_ON_ALL_FINISHED:
            shutdown = self._all_downloads_finished()
        elif self._method == constants.EXIT_ON_SEEDING_TIME:
            shutdown = self._stop_after_seeding()
        
        if shutdown:
            self._logger.debug("Initiating graceful shutdown at %i" % time.time())
            self._graceful_shutdown()
            
    def video_event_callback(self, d, event, params):
        '''This methdd will be called for every download for which a
        video event callback was registered. Its sole purpose is to determine,
        if the termination condition EXIT_ON_PLAYBACK_DONE is fulfilled. If
        the termination is not EXIT_ON_PLAYBACK_DONE, the method will
        immediately return. If not, it tries to determine the actual
        bitrate of the download. If that fails, it assumes a default
        bitrate. The bitrate is used to read <code>bitrate</code> amount
        of a data at a given time from the downloads input stream. To determine
        if the playback is done, it uses a rather simple but sufficient
        approach: If the total size of the data read from the stream >= the
        actual file size, the playback is considered to be done (the Tribler
        estimated playback time is calculated in a very similar way).
        
        Parameters:
            d -- Download object, representing an active download
            event -- Determines the video event
            params -- Dictionary which contains additional parameters
            
        Return:
            NoneType
        '''
        if self._method != constants.EXIT_ON_PLAYBACK_DONE:
            return
        
        self._logger.debug("Got a video event: %s" % event)

        content_length = d.get_def().get_length()
        bitrate = d.get_def().get_bitrate() or self._DEFAULT_BITRATE
        
        if event == "start":
            stream = params["stream"]
            grandtotal = 0L
            st = time.time()
            while True:
                total = 0
                while total < int(bitrate):
                    data = stream.read(int(bitrate))
                    total += len(data)
                grandtotal += total
#                et = time.time()
#                diff = et - st
#                grandrate = float(grandtotal) / diff
                done = float(grandtotal) / float(content_length) * 100
                self._logger.debug("Playback done: %d%%" % done)
                if done >= 100 and self._method == constants.EXIT_ON_PLAYBACK_DONE:
                    self._logger.debug("Initiating graceful shutdown at %i" % time.time())
                    self._graceful_shutdown()
                time.sleep(1.0)
        
    def _all_downloads_finished(self):
        '''Determines if the EXIT_ON_ALL_FINISHED termination condition
        is fulfilled.
        
        Return:
            True, if there was at least one download and all downloads
            have been finished. False, otherwise.
        '''
        finished = 0
        for torrent in self._downloads.keys():
            status, ts = self._downloads[torrent]
            if status == simpledefs.DLSTATUS_SEEDING:
                finished += 1
        return len(self._downloads.keys()) > 0 and finished == len(self._downloads.keys())

    def _stop_after_seeding(self):
        '''Determines if the EXIT_ON_SEEDING_TIME termination condition
        is fulfilled.
        
        Return:
            True, if the following conditions hold:
            * There was at least one download.
            * All downloads have been finished.
            * The download that became finished most recently was already
              MAX_SEEDING_TIME time in seeding mode.
            False, otherwise.
        '''
        # assure that every download is in DLSTATUS_SEEDING, otherwise we do not
        # have to perform further actions here
        if not self._all_downloads_finished():
            return False
        self._logger.debug("Stop after seeding call at: %i " % time.time())
        earliest_ts = 0
        # gather the time of the last update to DLSTATUS_SEEDING
        for torrent in self._downloads.keys():
            status, ts = self._downloads[torrent]
            if ts > earliest_ts:
                earliest_ts = ts
        # check if the earliest_ts had at least max_seeding_time time to seed
        self._logger.debug("Earliest ts: %i" % earliest_ts)
        self._logger.debug("Difference in s: %i" % (time.time() - earliest_ts))
        return time.time() - earliest_ts > self._max_seeding_time
    
    def _graceful_shutdown(self):
        '''Performs a graceful shutdown of the session itself, by calling the
        appropriate shutdown method and giving the session thread some time
        to properly shut the core of the client down. Afterwards, the given
        callback function (see __init__) gets called, allows to inject
        cleanup code after the client was shut down.
        
        Return:
            NoneType
        '''

        if self._callback is not None:
            self._callback()
            
#___________________________________________________________________________________________________

class ClientStatistics(PeerCallbackInterface):
    
    _out = None
    
    def __init__(self, directory, id):
        self._out = open('%sclient%s_statistics.out' % (directory, id), 'w')
        self.id = id
        self.directory = directory
        
    def __del__(self):
        if self._out is not None:
            self._out.close()
        
    def state_callback(self, ds):
        try:
            d = ds.get_download()
            progress = 100.0 * ds.get_progress()
            download = ds.get_current_speed(simpledefs.DOWNLOAD)
            upload = ds.get_current_speed(simpledefs.UPLOAD)
            torrent = d.get_def().get_name_as_unicode()
            status = ds.get_status()
            
            down_total, down_rate, up_total, up_rate = 0.0, 0.0, 0.0, 0.0
            if not ds.get_peerlist() is None:
                for p in ds.get_peerlist():
                    down_total += p['dtotal'] / 1024.0
                    down_rate  += p['downrate'] / 1024.0
                    up_total   += p['utotal'] / 1024.0
                    up_rate    += p['uprate'] / 1024.0
                    
            ts = time.time()
            line = "%i: %s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (ts,
                                                            torrent,
                                                            status,
                                                            download,
                                                            upload,
                                                            progress,
                                                            down_total,
                                                            down_rate,
                                                            up_total,
                                                            up_rate)
            self._out.write(line)
            self._out.flush()
        except:
            print_exc()
            
    def video_event_callback(self, d, event, params):
        pass
    
#___________________________________________________________________________________________________

class ClientHAPHandler(PeerCallbackInterface):
    def __init__(self, client_config):
        # neighbours is a multidimensional dictionary, where the first dimension's key
        # is the download for which upload/download statistics are gathered, and the second
        # dimension is the peer identifier. it stores and updates total upload and download
        # for traffic for active and non-active neighbours
        # example: neighbours[{torrend_id}][{peer_id}]['upload']
        # peer_id is comprised of ip address and port!
        self._neighbours = {}
        self._neighbour_ips = []
        self._client_config = client_config
        self._hap_client = HAP_WSClient(client_config.get_sis_hap_url(), None,
                                        client_config.get_port())
        self._last_report_sent = time.time()-client_config.get_hap_interval()
        self._logger = logging.getLogger("Status.HAP")
        self._last_period_peer_total = {}
    
    def state_callback(self, ds):

        torrent_id = common_utils.get_id(ds.get_download().get_def())
        
        if not ds.get_peerlist() is None:
            for peer in ds.get_peerlist():
                self._update_volume(torrent_id, peer['ip'], peer['dtotal'], peer['utotal'])
                
        # only send the report if a waiting period of hap_interval seconds passed by
        if not abs(self._last_report_sent - time.time()) >= self._client_config.get_hap_interval():
            return
        
        neighbour_stats = []
        new_last_period_peer_total = {}
        for peer in self._neighbour_ips:
            (download_volume, upload_volume) = self.aggregate_total_peer_traffic(peer)
            
            if download_volume == 0 and upload_volume == 0:
                continue
            
            if self._last_period_peer_total.has_key(peer):
                # we have old statistics for this peer
                old_dl, old_ul = self._last_period_peer_total[peer]
                
                if download_volume - old_dl == 0 and upload_volume - old_ul == 0:
                    continue
                
                neighbour_stats.append(HAPNeighbourStatisticsDTO(download_volume-old_dl, peer, upload_volume-old_ul))
                new_last_period_peer_total[peer] = (download_volume, upload_volume)
            else:
                # the peer must have joined during the current period
                neighbour_stats.append(HAPNeighbourStatisticsDTO(download_volume, peer, upload_volume))
                new_last_period_peer_total[peer] = (download_volume, upload_volume)
                
        # dont send a report if there are no neighbour stats
        if len(neighbour_stats) == 0:
            self._start_next_cycle(new_last_period_peer_total)
            return
        
        self._logger.info("Sending statistics to HAP...")
        self._hap_client.report_activity(neighbour_stats)
        self._start_next_cycle(new_last_period_peer_total)
        
    def _start_next_cycle(self, new_last_period_peer_total):
        self._last_report_sent = time.time()
        self._last_period_peer_total = new_last_period_peer_total
        # reset neighbours as well
        self._neighbours = {}
        self._neighbour_ips = []
            
    def _update_volume(self, torrent_id, peer_id, download, upload):
        '''Updates upload and download statistics for a given peer ID.
           Total upload and download are stored in KBytes.
        
           Arguments:
                torrent_id    --    Torrent ID in hexadecimal format
                peer_id       --    Peer ID that adheres to the format '<IP>'
                download      --    Current total download for given torrent and peer in bytes
                upload        --    Current total upload for given torrent and peer in bytes
        '''
        if not peer_id in self._neighbour_ips:
            self._neighbour_ips.append(peer_id)
        if not self._neighbours.has_key(torrent_id):
            self._neighbours[torrent_id] = {}
        if not self._neighbours[torrent_id].has_key(peer_id):
            self._neighbours[torrent_id][peer_id] = { 'upload'   :   0,
                                                      'download' :   0 }
        self._neighbours[torrent_id][peer_id]['upload'] = int(upload / 1024.0)
        self._neighbours[torrent_id][peer_id]['download'] = int(download / 1024.0)
        
    def aggregate_total_peer_traffic(self, peer_id):
        '''Calculates the total amount of upload and download traffic in KBytes for the peer
           identified by peer_id.
           
           Arguments:
               peer_id        -- The peer's ID (in this case, this should be the peer's
                                 IP address)
                                 
           Returns:
               A 2-tuple of the form (total_download, total_upload) where both values
               are given in KBytes.
        '''
        total_upload, total_download = 0.0, 0.0
        for torrent_id in self._neighbours.keys():
            if self._neighbours[torrent_id].has_key(peer_id):
                total_upload += self._neighbours[torrent_id][peer_id]['upload']
                total_download += self._neighbours[torrent_id][peer_id]['download']
        return (total_download, total_upload)
    
    def video_event_callback(self, d, event, params):
        pass
    
#___________________________________________________________________________________________________
import sys
class VoDClientHighRangeStatusHandler(PeerCallbackInterface):
    def __init__(self, communicator = None):
        self._communicator = communicator
        self._logger = logging.getLogger("Client.VodRangeHandler")      
        
    def get_communicator(self):
        return self.communicator
        
    def set_communicator(self, communicator):
        if self._communicator is not None:
            self._communicator.send_support_not_required()
        self._communicator = communicator
    
    def state_callback(self, ds):
        
        if not ds.get_download().sd:
            return

        if self._communicator is None or self._communicator.get_peer_id() != ds.get_download().sd.peerid:
            return
        
        bt1download = ds.get_download().sd.dow
        voddl = bt1download.voddownload
        storagewrapper = bt1download.storagewrapper
        
        if voddl is not None:
#            print >>sys.stderr, "VoDClientHighRangeStatusHandler called"
            left,right = voddl.videostatus.get_high_range()
            #get_download_range()
#            print >>sys.stderr, "High range (%i, %i), playbackpos=%i" % (left, right, voddl.videostatus.playback_pos) 
            
            missing_pieces = 0
            for i in xrange(left,right+1):
                if not storagewrapper.do_I_have(i):
                    missing_pieces += 1

            manually_pause = (voddl.videostatus.paused and not voddl.videostatus.autoresume) 
            gotall = (missing_pieces == 0)
            #TODO: missing condition: download finished!
            not_needed = (manually_pause or (gotall and voddl.enough_buffer()))
            
            # Alternative handling for supporter!
            bt1download.update_support_required(not not_needed) 
            
            # we are suffering if we prebuffering or the buffer is not full
            if not_needed:
                self._communicator.send_support_not_required()
            else:
                self._logger.info("Missing pieces: %i out of %i, expected buffering time=%i" % (missing_pieces, right-left+1, voddl.expected_buffering_time()))
                # our high prio set is not full yet, so request support
                self._communicator.send_support_required()
                
        else:
            print >>sys.stderr, "No VOD download!"
    
    def video_event_callback(self, d, event, params):
        pass