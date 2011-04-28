from SisClient.Cache.LocalFolderSelector import LocalFolderSelector
from SisClient.Utils.common_utils import convert_binary_string_to_hex
import SisClient.Cache.SIS.IoPService_client as WS
import logging, sys

'''
Created on 09.12.2009

@author: pussep
'''
class IoP_WSClientImpl(LocalFolderSelector):
    ''' This class uses the IoP API of the SIS controller to obtain
        torrent statistics and lists of local clients.
        It assumes that all torrents are available locally!
    '''
    def __init__(self, sis_iop_endpoint_url="http://localhost:8080/sis/IoPEndpoint"):
        self._logger = logging.getLogger("Cache.WebService")
        self._loc = WS.IoPServiceLocator()
        self._srv = self._loc.getIoPServicePort(sis_iop_endpoint_url)
        self.torrents = {}
    
    def set_torrent_dir(self, local_folder):
        self._load_torrents(local_folder)
    
    def report_activity(self, ip_addr, port, downloads):
        '''See IoP_WSClient.report_activity.'''
        
        class ActivityReport():
            def __init__(self, entries, extentions, ipAddress, port):
                self._entries = entries
                self._extentions = extentions
                self._ipAddress = ipAddress
                self._port = port
                
        class ActivityReportEntry():
            def __init__(self, torrentID, torrentURL, fileSize, progress):
                self._fileSize = fileSize
                self._progress = progress
                self._torrentID = torrentID
                self._torrentURL = torrentURL
                
        def build_report_entries(downloads):
            list_of_report_entries = []
            for download in downloads:
                if len(download) != 4:
                    self._logger.warning("Download tuple %s does not have the required fields. Skip." %
                                         download)
                    continue
                list_of_report_entries.append(ActivityReportEntry(download[0],
                                                                  download[1],
                                                                  download[2],
                                                                  download[3]))
            return list_of_report_entries

        request = WS.SisIoPPort_reportActivity()
        report = ActivityReport(build_report_entries(downloads),
                                [],
                                ip_addr,
                                port)
        request.set_element_arg0(report)
        self._srv.reportActivity(request)
    
    def retrieve_torrent_stats(self, max_requested_torrents=10):
        '''See IoP_WSClient.retrieve_torrent_stats.'''
        request = WS.SisIoPPort_getTorrentStats()
        request.set_element_arg0(max_requested_torrents)
        response_envelope = self._srv.getTorrentStats(request)
        torrent_statistics = response_envelope.get_element_stats()
        
        tstats_list = []
        for torrent in torrent_statistics:
            id = torrent.get_element_torrentHash()
            if id == '':
                continue
            url = torrent.get_element_torrentURL()
            rate = int(torrent.get_element_rate())
            tstats_list.append( (id, url, rate) )
        return tstats_list
    
    def retrieve_local_peers_for_active_torrents(self,
                                                 list_of_torrent_ids = [],
                                                 maximum_number_of_peers = 10,
                                                 include_seeds = False):
                
        class ActiveInTorrentsEntry(object):
            def __init__(self, infohash, maximum_number_of_peers, include_seeds):
                self._infohash = infohash
                self._maxPeers = maximum_number_of_peers
                self._seeds = include_seeds
        
        '''See IoP_WSClient.retrieve_local_peers_for_active_torrents.'''
        request = WS.SisIoPPort_activeInTorrents()

        list_of_entries = []
        for infohash in list_of_torrent_ids:
            entry = ActiveInTorrentsEntry(infohash, maximum_number_of_peers, include_seeds)
            list_of_entries.append(entry)
        request.set_element_arg0(list_of_entries)

        response_envelope = self._srv.activeInTorrents(request)
        response = response_envelope.get_element_response()
        
        torrent_dict = {}
        for torrent in response:
            torrent_id = torrent.get_element_torrentID()
            peer_list = []
            for peer in torrent.get_element_peers():
                peer_list.append((peer.get_element_ipAddress(),
                                  peer.get_element_port()))
            torrent_dict[torrent_id] = peer_list
        return torrent_dict
    
    def retrieve_configuration_parameters(self, my_own_ip="127.0.0.1"):
        '''See IoP_WSClient.retrieve_configuration_parameters.'''
        request = WS.SisIoPPort_getConfigParams()
        request.set_element_arg0(my_own_ip)
        response = self._srv.getConfigParams(request)
        config = response.get_element_config()
        
        list_of_getters = filter(lambda x: str(x).startswith('get_element_'), dir(config))
        config_dict = {}
        for getter in list_of_getters:
            tokens = getter.split('_')
            attribute_key = tokens[len(tokens)-1]
            config_dict[attribute_key] = getattr(config, getter)()
            
        return config_dict