from __future__ import with_statement

from BaseLib.Core import simpledefs

import os
import ConfigParser
import sys

from SisClient.Utils import common_utils
from SisClient.Common import constants
from SisClient.Common.PeerConfiguration import PeerConfiguration
from SisClient.Client import parse_client_cl
    
class ClientConfiguration(PeerConfiguration):
    def __init__(self):
        PeerConfiguration.__init__(self)
        
        self._state_directory = None
        self._mode_ps = constants.PS_MODE_NONE
        self._single_torrent = None
        self._exit_on = constants.EXIT_ON_ALL_FINISHED
        self._seeding_time = 15 # seconds
        self._activity_report_interval = 15 # seconds
        self._download_mode = simpledefs.DLMODE_NORMAL
        self._max_initiate = 10
        self._report_interval = 5.0
        self._logfile = 'player.log'
        self._hap_enabled = False
        self._hap_interval = 300
        self._supporter_seed = False
        self._supporter_ip = "127.0.0.1"
        
        self._mapping = {
            'ranking_source'    : (str, self.set_ranking_source, self.get_ranking_source),
            'mode_ns'        :   (str, self.set_ns_mode, self.get_ns_mode),
            'mode_ps'        :   (str, self.set_peer_selection_mode, self.get_peer_selection_mode),
            'locality_pref'  :   (float, self.set_locality_preference, self.get_locality_preference),
            'sis_url'        :   (str, self.set_sis_url, self.get_sis_url),
            'cache_interval' :   (float, self.set_rating_cache_interval, self.get_rating_cache_interval),
            'max_download_rate' : (int, self.set_download_limit, self.get_download_limit),
            'max_upload_rate'   : (int, self.set_upload_limit, self.get_upload_limit),
            'max_uploads'       : (int, self.set_max_upload_slots_per_download, self.get_max_upload_slots_per_download),
            'download_mode'     : (str, self.set_download_mode, self.get_download_mode),
            'max_connections'   : (int, self.set_connection_limit, self.get_connection_limit),
            #'max_initiate' : pass,
            #'min_uploads'  : pass,
            'torrent'           : (str, self.set_single_torrent, self.get_single_torrent),
            'report_to'         : (str, self.set_report_to, self.get_report_to),
            'serialization_method'  : (str, self.set_serialization_method, self.get_serialization_method),
            'compress_xml_reports'  : (lambda x: x == 'True', self.set_compress_xml_reports, self.get_compress_xml_reports),
            'report_interval'       : (float, self.set_report_interval, self.get_report_interval),
            'internal_id'           : (int, self.set_id, self.get_id),
            'activity_report_interval'      : (int, self.set_activity_report_interval, self.get_activity_report_interval),
            'hap_enabled'           : (lambda x: x == 'True', self.set_hap_enabled, self.is_hap_enabled),
            'hap_interval'          : (int, self.set_hap_interval, self.get_hap_interval), 
            'supporter_ips'         : (str, self.set_supporter_ip, self.get_supporter_ip)
            }
        
    def set_supporter_ip(self, supporter_ip):
        print >>sys.stderr, ""+supporter_ip
        self._supporter_ip = supporter_ip
        
    def get_supporter_ip(self):
        return self._supporter_ip
        
    def is_hap_enabled(self):
        return self._hap_enabled
    
    def set_hap_enabled(self, hap_enabled):
        self._hap_enabled = hap_enabled
        
    def get_hap_interval(self):
        return self._hap_interval
    
    def set_hap_interval(self, hap_interval):
        assert hap_interval >= 0
        self._hap_interval = hap_interval
        
    def get_sis_hap_url(self):
        if self.get_sis_url() != None:
            return common_utils.hap_url_from_sis_url(self.get_sis_url())
        
    def get_state_directory(self):
        return self._state_directory
    
    def set_state_directory(self, state_directory):
        self._state_directory = state_directory
        
    def get_peer_selection_mode(self):
        return self._mode_ps
    
    def set_peer_selection_mode(self, mode_ps):
        assert mode_ps in constants.PS_MODES_LIST
        self._mode_ps = mode_ps
        
    def get_single_torrent(self):
        return self._single_torrent
    
    def set_single_torrent(self, single_torrent):
        self._single_torrent = single_torrent
        
    def get_exit_on(self):
        return self._exit_on
    
    def set_exit_on(self, exit_on):
        assert exit_on in constants.EXIT_ON_LIST
        self._exit_on = common_utils.get_exit_on_from_string(exit_on)
        
    def get_seeding_time(self):
        return self._seeding_time
    
    def set_seeding_time(self, seeding_time):
        assert seeding_time >= 0
        self._seeding_time = seeding_time
        
    def get_activity_report_interval(self):
        return self._activity_report_interval
    
    def set_activity_report_interval(self, activity_report_interval):
        assert activity_report_interval >= 0
        self._activity_report_interval = activity_report_interval
        
    def get_download_mode(self):
        return self._download_mode
    
    def set_download_mode(self, download_mode):
        assert download_mode in constants.DOWNLOAD_MODES.keys()
        self._download_mode = constants.DOWNLOAD_MODES[download_mode]
        
    def get_max_initiate(self):
        return self._max_initiate
    
    def set_max_initiate(self, max_initiate):
        assert max_initiate >= 0
        self._max_initiate = max_initiate
        
    def is_supporter_seed(self):
        return self._supporter_seed
    
    def set_supporter_seed(self, supporter_seed):
        self._supporter_seed = supporter_seed
        
    def update_from_cl(self, cl=sys.argv[1:]):
        def set_attribute(attribute, func_name):
            if attribute is not None:
                func_name(attribute)
        (options, args) = parse_client_cl.parse_client_options(cl)
        
        if options.config is not None:
            self._update_from_static_configuration(options.config)

        set_attribute(options.is_supporter_seed, self.set_supporter_seed)
        set_attribute(options.port, self.set_port)
        set_attribute(options.id, self.set_id)
        set_attribute(options.directory, self.set_directory)
        set_attribute(options.temporary_state_directory, self.set_state_directory)
        set_attribute(options.logfile, self.set_logfile)
        set_attribute(options.mode_ps, self.set_peer_selection_mode)
        set_attribute(options.mode_ns, self.set_ns_mode)
        set_attribute(options.ranking_source, self.set_ranking_source)
        set_attribute(options.sis_url, self.set_sis_url)
        set_attribute(options.upload, self.set_upload_limit)
        set_attribute(options.download, self.set_download_limit)
        set_attribute(options.single_torrent, self.set_single_torrent)
        set_attribute(options.report_to, self.set_report_to)
        set_attribute(options.activity_report_interval, self.set_activity_report_interval)
        set_attribute(options.delete_directories, self.set_delete_directories)
        set_attribute(options.hap_enabled, self.set_hap_enabled)
        set_attribute(options.hap_interval, self.set_hap_interval)
        
        if options.exit is not None:
            set_attribute(options.exit[0], self.set_exit_on)
            if len(options.exit) == 2:                
                set_attribute(int(options.exit[1]), self.set_seeding_time)            
            
        if options.ip_prefix is not None:
            set_attribute(options.ip_prefix.split(';'), self.set_ip_prefixes)
    
    def _update_from_static_configuration(self, static_configuration_file):
        def set_attribute(attribute, func_name):
            if attribute is not None:
                func_name(attribute)
        
        if not os.access(static_configuration_file, os.F_OK):
            print >>sys.stderr, "Configuration file [%s] does not exist or not accessible"%(static_configuration_file)
            return
        
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(static_configuration_file)

        cache_dict = {}
        for section in config_parser.sections():
            for (name, value) in config_parser.items(section):
                cache_dict[name] = value

        def is_static_configuration_consistent():
            # throws an assertion error if the static configuration file contains a key-value
            # pair that should be in there and was properly introduced by mispelling an admissible
            # key-value pair
            for conf_key in cache_dict.keys():
                assert conf_key in self._mapping.keys(), "check for %s in %s" % (conf_key, self._mapping.keys())
        
        def set_attribute_if_present(name):
            if cache_dict.has_key(name):
                set_attribute(self._mapping[name][0](cache_dict[name]), self._mapping[name][1])
        
        is_static_configuration_consistent()        
        for m in self._mapping.keys():
            set_attribute_if_present(m)