from __future__ import with_statement

import logging
import os
import ConfigParser
import sys

from SisClient.Utils import net_utils
from SisClient import parse_cl
from SisClient.Common import constants
from SisClient.Common.PeerConfiguration import PeerConfiguration
from SisClient.Cache.IoP_WSClientImpl import IoP_WSClientImpl
from SisClient.Common.PeerConfiguration import ConfigurationException

class CacheConfiguration(PeerConfiguration):
    def __init__(self):
        PeerConfiguration.__init__(self)

        self._torrent_selection_interval = 30
        self._rate_interval = 30
        self._max_torrents = 10
        self._min_leechers = 0
        self._min_local_leechers = 0
        self._min_ulfactor = 0.6
        self._torrent_selection_mechanism = 'local_folder'
        self._torrent_directory = 'torrents'
        self._rate_management = 'equal'
        self._replacement_strategy = constants.RP_FIFO
        self._max_downloads = 5
        self._ranking_source = constants.RS_IP_PRE
        self._directory = "iop_data"
        self._space_limit = 100
        self._cache_console = False
        self._establish_remote_connections = True
        self._stay_in_torrents = 4
        self._ns_mode = constants.NS_MODE_ENABLE
        self._locality_pref = float(1)
        self._logfile = 'iop.log'
        #TODO: the meaning here is different than for a normal client, since cache divides connections across all torrents! Better to use another name for it?
        self._connection_limit = 10000
        #TODO: some default values might be missing!!! Cf. self._mapping
        
        self._logger = logging.getLogger("Cache.Configuration")

        self._mapping = {
                   'torrent_selection_interval' :   (int, self.set_torrent_selection_interval, self.get_torrent_selection_interval),
                   'torrent_selection_mechanism' :  (str, self.set_torrent_selection_mechanism, self.get_torrent_selection_mechanism),
                   'max_torrents'               :   (int, self.set_max_torrents, self.get_max_torrents),
                   'min_leechers'               :   (int, self.set_min_leechers, self.get_min_leechers),
                   'torrent_directory'          :   (str, self.set_torrent_directory, self.get_torrent_directory),
                   'rate_management'            :   (str, self.set_rate_management, self.get_rate_management),
                   'replacement_strategy'       :   (str, self.set_replacement_strategy, self.get_replacement_strategy),
                   'min_ulfactor'               :   (float, self.set_min_ulfactor, self.get_min_ulfactor),
                   'max_downloads'              :   (int, self.set_max_downloads, self.get_max_downloads),
                   #TODO #944: Test whether ip prefixes are properly parsed!!!
                   'ip_prefix'                  :   (lambda x: x.split(";"), self.set_ip_prefixes, self.get_ip_prefixes),
                   'rate_interval'              :   (int, self.set_rate_interval, self.get_rate_interval),
                   'report_interval'            :   (float, self.set_report_interval, self.get_report_interval),
                   'compress_xml_reports'       :   (lambda x: x == 'True', self.set_compress_xml_reports, self.get_compress_xml_reports),
                   'serialization_method'       :   (str, self.set_serialization_method, self.get_serialization_method),
                   'space_limit'                :   (int, self.set_space_limit, self.get_space_limit),
                   'cache_directory'            :   (str, self.set_directory, self.get_directory),
                   'download_limit'             :   (int, self.set_download_limit, self.get_download_limit),
                   'upload_limit'             :   (int, self.set_upload_limit, self.get_upload_limit),
                   'sis_url'                    : (str, self.set_sis_url, self.get_sis_url),
                   'max_uploads_per_dl'         : (int, self.set_max_upload_slots_per_download, self.get_max_upload_slots_per_download),
                   'stay_in_torrents'           : (int, self.set_stay_in_torrents, self.get_stay_in_torrents)
    }
        
    def get_torrent_selection_interval(self):
        '''
        Inteval to perform torrent selection (in seconds)
        '''
        return self._torrent_selection_interval
    
    def set_torrent_selection_interval(self, torrent_selection_interval):
        assert torrent_selection_interval >= 0
        self._torrent_selection_interval = torrent_selection_interval
        
    def get_max_torrents(self):
        return self._max_torrents
    
    def set_max_torrents(self, max_torrents):
        self._max_torrents = max_torrents
        
    def get_min_leechers(self):
        return self._min_leechers
    
    def set_min_leechers(self, min_leechers):
        assert min_leechers >= 0
        self._min_leechers = min_leechers
        
    def get_min_local_leechers(self):
        return self._min_local_leechers
    
    def set_min_local_leechers(self, min_local_leechers):
        assert min_local_leechers >= 0
        self._min_local_leechers = min_local_leechers
        
    def get_min_ulfactor(self):
        return self._min_ulfactor
    
    def set_min_ulfactor(self, min_ulfactor):
        assert min_ulfactor >= 0.0
        self._min_ulfactor = min_ulfactor
        
    def get_torrent_selection_mechanism(self):
        return self._torrent_selection_mechanism
    
    def set_torrent_selection_mechanism(self, torrent_selection):
        assert torrent_selection in constants.SELECTION_MODE_LIST
        self._torrent_selection_mechanism = torrent_selection
        
    def get_torrent_directory(self):
        return self._torrent_directory
    
    def set_torrent_directory(self, torrent_directory):
        self._torrent_directory = torrent_directory
        
    def get_rate_management(self):
        return self._rate_management
    
    def set_rate_management(self, rate_management):
        # TODO: add assertions
        self._rate_management = rate_management
        
    def get_replacement_strategy(self):
        return self._replacement_strategy
    
    def set_replacement_strategy(self, replacement_strategy):
        assert replacement_strategy in constants.RP_LIST
        self._replacement_strategy = replacement_strategy
    
    def get_max_downloads(self):
        return self._max_downloads
    
    def set_max_downloads(self, max_downloads):
        assert max_downloads >= 0
        self._max_downloads = max_downloads
        
    def get_rate_interval(self):
        return self._rate_interval
    
    def set_rate_interval(self, rate_interval):
        assert rate_interval >= 0
        self._rate_interval = rate_interval
        
    def get_space_limit(self):
        return self._space_limit
    
    def set_space_limit(self, space_limit):
        assert space_limit >= 0
        self._space_limit = space_limit
        
    def has_cache_console(self):
        return self._cache_console
    
    def set_cache_console(self, cache_console):
        self._cache_console = cache_console
        
    def establish_remote_connections(self):
        return self._establish_remote_connections
        
    def set_establish_remote_connections(self, establish_remote_connections):
        self._establish_remote_connections = establish_remote_connections
        
    def get_stay_in_torrents(self):
        return self._stay_in_torrents
    
    def set_stay_in_torrents(self, stay_in_torrents):
        assert stay_in_torrents >= 0
        self._stay_in_torrents = stay_in_torrents
        
    def update_from_cl(self, cl=sys.argv[1:]):
        ''' Update configuration using the given command line parameters.
        If the sis config is set in the config file (or cmd options)
        also load the config options through the SIS IOP config API.
        Return True if SIS IoP API was used, and False otherwise
        '''
        def set_attribute(attribute, func_name):
            if attribute is not None:
                func_name(attribute)
        (options, args) = parse_cl.parse_cache_options(cl)
        self._logger.info("Parse arguments %s" % cl)
        
        if options.config is not None:
            self._update_from_static_configuration(options.config)
            
        set_attribute(options.sis_url, self.set_sis_url)
        
        if self.get_sis_url() is not None:
            self._update_from_sis()
            use_sis = True
        else:
            use_sis = False
        
        set_attribute(options.port, self.set_port)
        set_attribute(options.directory, self.set_directory)
        set_attribute(options.torrentdir, self.set_torrent_directory)
        set_attribute(options.downlimit, self.set_download_limit)
        set_attribute(options.uplimit, self.set_upload_limit)
        set_attribute(options.spacelimit, self.set_space_limit)
        set_attribute(options.conlimit, self.set_connection_limit)
        set_attribute(options.logfile, self.set_logfile)
        set_attribute(options.id, self.set_id)
        set_attribute(options.ranking_source, self.set_ranking_source)
        set_attribute(options.report_to, self.set_report_to)
        set_attribute(options.cache_console, self.set_cache_console)
        
        return use_sis
            
    def _update_from_static_configuration(self, static_configuration_file):
        
        if not os.path.isfile(static_configuration_file):
            self._logger.error("Configuration file %s must exist" % static_configuration_file)
            raise ConfigurationException("Configuration file %s must exist" % static_configuration_file)
            
        def set_attribute(attribute, func_name):
            if attribute is not None:
                func_name(attribute)
        
        if not os.access(static_configuration_file, os.F_OK):
            return
        
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(static_configuration_file)

        cache_dict = {}
        for (name, value) in config_parser.items(constants.CACHING_SECTION_NAME):
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

    def _update_from_sis(self):
        def set_attribute(attribute, func_name):
            if attribute is not None:
                func_name(attribute)
        
        ws_client = IoP_WSClientImpl(self.get_sis_iop_url())
        
        config_dict = {}
        try:
            config_dict = ws_client.retrieve_configuration_parameters(net_utils.get_own_ip_addr())
            self._logger.warning("Config dict returned was: %s" % config_dict)
            
            if len(config_dict.keys()) == 0:
                self._logger.warning("Received an empty dict. Cache configuration was not updated.")
                return

            max_torrents = int(min( float(config_dict.get('u')) / float(config_dict.get('ulow')),
                                    float(config_dict.get('d')) / float(config_dict.get('dlow'))))
            
            sis_modes = { 'Collaboration' : constants.SELECTION_MODE_IOP,
                          'Plain'         : constants.SELECTION_MODE_LOCAL,
                          'Combination'   : constants.SELECTION_MODE_LOCAL }

            set_attribute(config_dict.get('t'), self.set_torrent_selection_interval)
            set_attribute(config_dict.get('u'), self.set_upload_limit)
            set_attribute(config_dict.get('d'), self.set_download_limit)
            set_attribute(config_dict.get('slots'), self.set_max_upload_slots_per_download)
            set_attribute(config_dict.get('remotes'), self.set_establish_remote_connections)
            set_attribute(config_dict.get('x'), self.set_stay_in_torrents)
            set_attribute(config_dict.get('localIPs'), self.set_ip_prefixes)
            set_attribute(sis_modes[config_dict.get('mode')], self.set_torrent_selection_mechanism)
            set_attribute(max_torrents, self.set_max_torrents)
            set_attribute(max_torrents, self.set_max_downloads)
        except:
            self._logger.error("Failed to retrieve cache configuration from SIS at %s" %
                               self.get_sis_iop_url())
            self._logger.error("Cache configuration was not updated.", exc_info=True)
            self._logger.error("Received config dict was: %s" % config_dict)

            raise ConfigurationException("Failed to retrieve cache configuration from SIS at %s" %
                               self.get_sis_iop_url())
            
            return
        
    def _default_config(self):
        config = ConfigParser.SafeConfigParser()
        config.add_section(constants.CACHING_SECTION_NAME)
        for (key, data) in self.mapping.items():
            getter = data[2]
            value = str(getter())
            config.set(constants.CACHING_SECTION_NAME, key, value)
        return config
    
#___________________________________________________________________________________________________
# MAIN
    
if __name__ == '__main__':
    print "Create reference config file with default values"
    print "Usage python %s <config-file-name>" % sys.argv[0]
    out = sys.argv[1]
    config = CacheConfiguration()._default_config()
    with open(out, 'w') as configfile:
        config.write(configfile)
    print "Default configuration was written into file: %s" % out

