import logging
import logging.config
import os
import sys
import time
import tempfile

from BaseLib.Core.simpledefs import UPNPMODE_DISABLED
from BaseLib.Core.simpledefs import UPLOAD, DOWNLOAD, DLMODE_VOD
from BaseLib.Core.API import SessionStartupConfig
from BaseLib.Core.API import Session
from BaseLib.Core.API import TorrentDef
from BaseLib.Core.API import DownloadStartupConfig

from SisClient.Client.ClientConfiguration import ClientConfiguration
from SisClient.Common import constants
from SisClient.Testbed.Utils.utils import set_exit_handler
from SisClient.Testbed.Utils.utils import files_list
from SisClient.Testbed.Utils.utils import FileUtils

from SisClient.Common.CommonPeerHandlers import PeerActivityReportEmitter
from SisClient.Common.CommonPeerHandlers import PeerHTTPReporter
from SisClient.Common.CommonPeerHandlers import PeerLocalReporter
from SisClient.Common.CommonPeerHandlers import PeerReporter
from SisClient.Common.PeerCallbackHandlers import PeerCallbackHandlers
from SisClient.Client.ClientCallbackHandlers import ClientStatistics
from SisClient.Client.ClientCallbackHandlers import ClientUptimeHandler
from SisClient.Client.ClientCallbackHandlers import ClientHAPHandler
from SisClient.Utils import net_utils
from SisClient.Utils import common_utils
from SisClient.RankingPolicy import RankingPolicy
from SisClient.PeerSelection import NeighborSelection, BiasedUnchoking

class Client(object):
    def __init__(self, client_config):
        self._config = client_config
        self._logger = logging.getLogger(self._get_name())
        self._local_reporter = None
        
        if self._config.get_logfile() is not None:
            logfile_directory = FileUtils.get_path_from_full_filename(self._config.get_logfile())
            if self._config.get_logfile().find(os.path.normcase('/')) > -1 and \
                    not os.access(logfile_directory, os.F_OK):
                os.mkdir(logfile_directory)
        
        torrent_file = self._config.get_single_torrent()
        if torrent_file is not None:
            if not os.access(torrent_file, os.F_OK):
                self._logger.error("The specified torrent file %s does not exist." % torrent_file)
                self._on_exit()
        
    def _get_name(self):
        return "%s.%i" % (self.__class__.__name__, self._config.get_id())
    
    def _cleanup(self, signal=None, func=None):
        if self._config.get_delete_directories():
            FileUtils.remove_directory_recursively(self._config.get_directory())
            FileUtils.remove_directory_recursively(self._config.get_state_directory())
            self._logger.warn("Removed directories %s and %s" % (self._config.get_directory(),
                                                                 self._config.get_state_directory()))
        
    def start_client(self):
        self._setup_client()
        self._start_downloads()
        set_exit_handler(self._on_exit)
        
        try:
            while True:
                time.sleep(5)
            time.sleep(self._config.get_report_interval())
        except KeyboardInterrupt:
            pass
        finally:
            self._on_exit()
            
    def _setup_client(self):
        def setup_directories():
            if not os.access(self._config.get_directory(), os.F_OK):
                os.mkdir(self._config.get_directory())
            if self._config.get_state_directory():
                if not os.access(self._config.get_state_directory(), os.F_OK):
                    os.mkdir(self._config.get_state_directory())
            else:
                state_dir = tempfile.mkdtemp()
                self._config.set_state_directory(state_dir)
        
        def setup_scfg():
            scfg = SessionStartupConfig()
            scfg.set_state_dir(self._config.get_state_directory())
            scfg.set_listen_port(self._config.get_port())
            scfg.set_overlay(False)
            scfg.set_megacache(False)
            scfg.set_upnp_mode(UPNPMODE_DISABLED)
            return scfg
        
        def setup_callback_handlers(session, scfg):
            self._handlers = PeerCallbackHandlers(self._get_name(), self._config.get_report_interval())
            self._handlers.register_handler(PeerReporter(self._get_name()))
            self._handlers.register_handler(ClientStatistics(self._config.get_directory(),
                                                       self._config.get_id()))
            
            if self._config.is_hap_enabled():
                self._logger.info("HAP support enabled")
                self._handlers.register_handler(ClientHAPHandler(self._config))
            
            if self._config.get_sis_url() != None:
                ip_addr = net_utils.get_own_ip_addr()
                self._handlers.register_handler(PeerActivityReportEmitter(
                    (ip_addr, self._config.get_port()),
                    self._config.get_activity_report_interval(),
                    sis_iop_endpoint_url=self._config.get_sis_iop_url()))
                
            if self._config.get_exit_on() == constants.EXIT_ON_ALL_FINISHED:
                self._handlers.register_handler(ClientUptimeHandler(session,
                                                              method=constants.EXIT_ON_ALL_FINISHED,
                                                              callback=self._on_exit))
            elif self._config.get_exit_on() == constants.EXIT_ON_PLAYBACK_DONE:
                self._handlers.register_handler(ClientUptimeHandler(session,
                                                              method=constants.EXIT_ON_PLAYBACK_DONE,
                                                              callback=self._on_exit))
            elif self._config.get_exit_on() == constants.EXIT_ON_SEEDING_TIME:
                self._handlers.register_handler(ClientUptimeHandler(session,
                                                              method=constants.EXIT_ON_SEEDING_TIME,
                                                              max_seeding_time=self._config.get_seeding_time(),
                                                              callback=self._on_exit))
                
            if self._config.get_report_to() is not None:
                if self._config.get_report_to() == 'local_report':
                    self._local_reporter = PeerLocalReporter(self._get_name(),
                                                         self._config.get_id(),
                                                         session,
                                                         self._config.get_directory())
                    self._handlers.register_handler(self._local_reporter)
                else:
                    self._handlers.register_handler(PeerHTTPReporter(self._get_name(),
                                                                 self._config.get_id(),
                                                                 self._config.get_report_to(),
                                                                 scfg,
                                                                 self._config.get_compress_xml_reports(),
                                                                 self._config.get_serialization_method(),
                                                                 report_interval=self._config.get_report_interval()))
                
        setup_directories()
        self._logger.info("Client directory is at %s" % self._config.get_directory())
        self._logger.info("Client state directory is at %s" % self._config.get_state_directory())
        scfg = setup_scfg()
        self._session = Session(scfg)
        self._session.set_supporter_seed(self._config.is_supporter_seed())#TODO: parameterize!!!
        self._logger.error("Supporter IPs are: "+self._config.get_supporter_ip())
        self._session.set_supporter_ips(self._config.get_supporter_ip())
        setup_callback_handlers(self._session, scfg)
        
        source = self._config.get_ranking_source()
        endpoint = self._config.get_sis_client_endpoint()
        ranking = RankingPolicy.selectRankingSource(source, conf=self._config)
        NeighborSelection.createMechanism(self._config.get_ns_mode(), ranking,
                                          locality_pref=self._config.get_locality_preference())
        BiasedUnchoking.BiasedUnchoking(self._config.get_peer_selection_mode(), ranking) 
        
    def _start_downloads(self):
        torrent_files = []
        if self._config.get_single_torrent() is not None:
            torrent_files.append(self._config.get_single_torrent())
        else:
            torrent_files = files_list(self._config.get_directory(), [constants.TORRENT_DOWNLOAD_EXT, constants.TORRENT_VOD_EXT])
        if len(torrent_files) == 0:
            self._logger.error("No torrents found.")
            self._on_exit()
            os._exit(1)
        for torrent in torrent_files:
            self._start_download(torrent)
            
    def _start_download(self, torrent):
        tdef = TorrentDef.load(torrent)
        dscfg = DownloadStartupConfig()
        #disable PEX protocol, otherwise it will crash if two clients are running on the same machine!
        #dscfg.set_ut_pex_max_addrs_from_peer(0)
        
        dscfg.set_dest_dir(self._config.get_directory())
        if common_utils.has_torrent_video_files(tdef) and not self._config.is_supporter_seed():
            dscfg.set_video_event_callback(self._handlers.video_event_callback)
        self._logger.warn("Download directory: " + dscfg.get_dest_dir())
        dscfg.set_max_speed(UPLOAD, self._config.get_upload_limit())
        dscfg.set_max_speed(DOWNLOAD, self._config.get_download_limit())
        con_lim = self._config.get_connection_limit()
        dscfg.set_max_conns(con_lim)
        dscfg.set_max_conns_to_initiate((con_lim+1)/2)
        dscfg.set_min_peers((con_lim+2)/3)
        dscfg.set_max_uploads(self._config.get_max_upload_slots_per_download())
        dscfg.set_peer_type("G")
        
        self._logger.warn("Files available: %s" % tdef.get_files())
        
        if dscfg.get_mode() == DLMODE_VOD:
            self._logger.warn("RUN in streaming mode")
            if tdef.is_multifile_torrent():
                for file in tdef.get_files():
                    if file.endswith(".avi"):
                        dscfg.set_selected_files([file])
                        break
        else:
            self._logger.warn("RUN in file sharing mode")
            
        d = self._session.start_download(tdef, dscfg)
        d.set_state_callback(self._handlers.state_callback, getpeerlist=True)
      
    def _on_exit(self, signal=None, func=None):
        if self._local_reporter is not None:
            self._local_reporter.write_stats()
        # stop all active downloads
        for download in self._session.get_downloads():
            download.stop()
        # shutting down session
        self._session.shutdown(checkpoint=False, gracetime=2.0)
        # call the provided method (cleanup purposes)
        self._cleanup(signal, func)
        os._exit(0)
    
#___________________________________________________________________________________________________
# MAIN
    
if __name__ == "__main__":
    logging.config.fileConfig("config/log_client.conf")
    client_config = ClientConfiguration()
    client_config.update_from_cl(sys.argv[1:])
    
    if client_config.get_logfile() is not None:
        print >>sys.stderr, "Using logfile: %s" % client_config.get_logfile()
        common_utils.setup_client_file_logger(client_config.get_logfile())
    
    client = Client(client_config)
    client.start_client()