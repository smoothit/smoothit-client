import logging
import random

from BaseLib.Core.defaults import dldefaults

from SisClient.Common import constants
from SisClient.Utils import ipaddr_utils
from SisClient.Utils import common_utils

class ConfigurationException(Exception):
    ''' Thrown if configuration failed! '''
    def __init__(self, value):
        self.parameter = value
        
    def __str__(self):
        return repr(self.parameter)

class PeerConfiguration(object):
    def __init__(self):
        self._port = random.randint(constants.PORT_RANGE_LOWER_BOUND,
                                    constants.PORT_RANGE_UPPER_BOUND)
        self._id = random.randint(0, 10000)
        self._directory = "peer_data"
        self._logfile = None
        self._ns_mode = constants.NS_MODE_NONE
        self._ranking_source = constants.RS_NONE
        self._sis_url = None
        self._upload_limit = 32
        self._download_limit = 32
        self._report_to = None
        self._report_interval = 10.0
        self._ip_prefixes = ['127.0.0.1/24']
        self._compress_xml_reports = False
        self._serialization_method = 'xml'
        self._locality_pref = float(0.9)
        self._max_upload_slots_per_download = dldefaults['max_uploads']
        self._connection_limit = dldefaults['max_connections']
        self._delete_directories = False
        self._rating_cache_interval = 15 # seconds#
        
    def get_delete_directories(self):
        return self._delete_directories
    
    def set_delete_directories(self, modifier):
        self._delete_directories = modifier
        
    def get_id(self):
        return self._id
    
    def set_id(self, id):
        assert id >= 0
        self._id = id
        
    def get_port(self):
        return self._port
    
    def set_port(self, port):
        assert port >= 1024
        assert port <= 65535
        self._port = port
        
    def get_directory(self):
        return self._directory
    
    def set_directory(self, directory):
        self._directory = directory
        
    def get_logfile(self):
        return self._logfile
        
    def set_logfile(self, logfile):
        self._logfile = logfile
        
    def get_ns_mode(self):
        return self._ns_mode
    
    def set_ns_mode(self, ns_mode):
        assert ns_mode in constants.NS_MODES_LIST
        self._ns_mode = ns_mode
        
    def get_ranking_source(self):
        return self._ranking_source
        
    def set_ranking_source(self, ranking_source):
        assert ranking_source in constants.RS_MODES_LIST
        self._ranking_source = ranking_source
        
    def get_sis_url(self):
        return self._sis_url
    
    def set_sis_url(self, sis_url):
        # TODO: assertion for sis_url format!
        assert sis_url.endswith("/sis")
        self._sis_url = sis_url
        
    def get_sis_client_endpoint(self):
        return common_utils.client_url_from_sis_url(self.get_sis_url())
        
    def get_sis_iop_url(self):
        if self.get_sis_url() != None:
            return common_utils.iop_url_from_sis_url(self.get_sis_url())
        
    def get_download_limit(self):
        return self._download_limit
        
    def set_download_limit(self, download_limit):
        assert download_limit >= 0
        self._download_limit = download_limit
        
    def get_upload_limit(self):
        return self._upload_limit
        
    def set_upload_limit(self, upload_limit):
        assert upload_limit >= 0
        self._upload_limit = upload_limit
        
    def get_report_to(self):
        return self._report_to
        
    def set_report_to(self, report_to):
        # TODO: add assertion (format)
        self._report_to = report_to
        
    def get_report_interval(self):
        return self._report_interval
    
    def set_report_interval(self, report_interval):
        self._report_interval = report_interval
        
    def get_ip_prefixes(self):
        return self._ip_prefixes
    
    def set_ip_prefixes(self, ip_prefixes):
        assert type(ip_prefixes) == list
        tmp_list = []
        for i in xrange(len(ip_prefixes)):
            stripped_ip = ip_prefixes[i].strip()
            assert ipaddr_utils.is_reference_ip_addr_admissible(stripped_ip)
            tmp_list.append(stripped_ip)
        self._ip_prefixes = tmp_list
        
    def get_serialization_method(self):
        return self._serialization_method
        
    def set_serialization_method(self, serialization_method):
        # TODO: assertions!
        self._serialization_method = serialization_method
        
    def get_compress_xml_reports(self):
        return self._compress_xml_reports
    
    def set_compress_xml_reports(self, compress_xml_reports):
        self._compress_xml_reports = compress_xml_reports
        
    def get_locality_preference(self):
        return self._locality_pref
        
    def set_locality_preference(self, locality_preference):
        self._locality_pref = locality_preference
        
    def get_rating_cache_interval(self):
        return self._rating_cache_interval
    
    def set_rating_cache_interval(self, rating_cache_interval):
        assert rating_cache_interval >= 0
        self._rating_cache_interval = rating_cache_interval
        
    def get_max_upload_slots_per_download(self):
        return self._max_upload_slots_per_download

    def set_max_upload_slots_per_download(self, value):
        assert value >= 0 and value < 20, value
        self._max_upload_slots_per_download = value
        
    def get_connection_limit(self):
        return self._connection_limit
    
    def set_connection_limit(self, connection_limit):
        assert connection_limit >= 0
        self._connection_limit = connection_limit