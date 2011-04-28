import unittest
import logging
import os

from BaseLib.Core import simpledefs
from SisClient.Cache.CacheConfiguration import CacheConfiguration
from SisClient.Client.ClientConfiguration import ClientConfiguration
from SisClient.Common import constants

class TestConfig(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_cache_update_from_cl_only(self):
        ''' 
        Test config from command line only.
        '''
        test_commandline = "--port=4000 --directory=test_cache --torrentdir=test_torrent_dir " + \
                           "--downlimit=256 --uplimit=256 --spacelimit=4000 --conlimit=20 " + \
                           "--logfile=test_cache.log --id=34 --neighbour_selection=enable " + \
                           "--ranking_source=ip_pre " + \
                           "--report_to=http://localhost:8444 --console --loglevel=DEBUG"
        
        cache_config = CacheConfiguration()
        used_sis = cache_config.update_from_cl(test_commandline.split(" "))
        self.assertFalse(used_sis)
        
        self.assertEquals(4000, cache_config.get_port())
        self.assertEquals("test_cache", cache_config.get_directory())
        self.assertEquals("test_torrent_dir", cache_config.get_torrent_directory())
        self.assertEquals(256, cache_config.get_download_limit())
        self.assertEquals(256, cache_config.get_upload_limit())
        self.assertEquals(4000, cache_config.get_space_limit())
        self.assertEquals(20, cache_config.get_connection_limit())
        self.assertEquals("test_cache.log", cache_config.get_logfile())
        self.assertEquals(34, cache_config.get_id())
        self.assertEquals(constants.NS_MODE_ENABLE, cache_config.get_ns_mode())
        self.assertEquals(constants.RS_IP_PRE, cache_config.get_ranking_source())
        self.assertEquals(None, cache_config.get_sis_url())
        self.assertEquals(None, cache_config.get_sis_iop_url())
        self.assertEquals("http://localhost:8444", cache_config.get_report_to())
        self.assertEquals(True, cache_config.has_cache_console())
    
    def test_cache_config_from_sis_with_cl_update(self):
        ''' 
        Test config from command line and SIS server.
        '''
        test_commandline = "--port=4000 --directory=test_cache --torrentdir=test_torrent_dir " + \
                           "--downlimit=256 --uplimit=256 --spacelimit=4000 --conlimit=20 " + \
                           "--logfile=test_cache.log --id=34 --neighbour_selection=enable " + \
                           "--ranking_source=ip_pre --sis_url=http://localhost:8080/sis " + \
                           "--report_to=http://localhost:8444 --console --loglevel=DEBUG"
        
        cache_config = CacheConfiguration()
        used_sis = cache_config.update_from_cl(test_commandline.split(" "))
        self.assertTrue(used_sis)
        
        self.assertEquals(4000, cache_config.get_port())
        self.assertEquals("test_cache", cache_config.get_directory())
        self.assertEquals("test_torrent_dir", cache_config.get_torrent_directory())
        self.assertEquals(256, cache_config.get_download_limit())
        self.assertEquals(256, cache_config.get_upload_limit())
        self.assertEquals(4000, cache_config.get_space_limit())
        self.assertEquals(20, cache_config.get_connection_limit())
        self.assertEquals("test_cache.log", cache_config.get_logfile())
        self.assertEquals(34, cache_config.get_id())
        self.assertEquals(constants.NS_MODE_ENABLE, cache_config.get_ns_mode())
        self.assertEquals(constants.RS_IP_PRE, cache_config.get_ranking_source())
        self.assertEquals("http://localhost:8080/sis", cache_config.get_sis_url())
        self.assertEquals("http://localhost:8080/sis/IoPEndpoint", cache_config.get_sis_iop_url())
        self.assertEquals("http://localhost:8444", cache_config.get_report_to())
        self.assertEquals(True, cache_config.has_cache_console())
    
    def test_cache_update_from_cl_with_static(self):
        ''' 
        Test config from config file only.
        '''
        cwd = os.path.dirname(os.path.realpath(__file__))
        static_conf_file = os.path.join(cwd, "test_cache_static.conf")
        if not os.access(static_conf_file, os.F_OK):
            self.fail("Unable to locate test_cache_static.conf")
        
        test_commandline = "--config=%s" % static_conf_file
        
        cache_config = CacheConfiguration()
        used_sis = cache_config.update_from_cl(test_commandline.split(" "))
        self.assertFalse(used_sis)
        
        self.assertEquals(15, cache_config.get_torrent_selection_interval())
        self.assertEquals(500, cache_config.get_max_torrents())
        self.assertEquals(1, cache_config.get_min_leechers())
        self.assertEquals("test_cache_torrents", cache_config.get_torrent_directory())
        self.assertEquals("equal", cache_config.get_rate_management())
        self.assertEquals("fifo", cache_config.get_replacement_strategy())
        self.assertEquals(0.6, cache_config.get_min_ulfactor())
        self.assertEquals(100, cache_config.get_max_downloads())
        self.assertEquals(['127.0.0.1/32', '88.158.32.2/16'], cache_config.get_ip_prefixes())
        self.assertEquals(20, cache_config.get_rate_interval())
    
    def test_cache_update_from_sis_only(self):
        ''' 
        Test config from config file and SIS.
        '''
        test_commandline = "--sis_url=http://localhost:8080/sis"
        
        cache_config = CacheConfiguration()
        used_sis = cache_config.update_from_cl(test_commandline.split(" "))
        self.assertTrue(used_sis)
        
        print "No way to obtain meaningful iop parameters from SIS right now, Skip assertions."
        return 
        self.assertEquals(300, cache_config.get_torrent_selection_interval())
        self.assertEquals(1024, cache_config.get_upload_limit())
        self.assertEquals(2048, cache_config.get_download_limit())
        self.assertEquals(5, cache_config.get_connection_limit())
        self.assertEquals(True, cache_config.establish_remote_connections())
        
    def test_client_config_from_cl(self):
        cmdline = '--port=8800 --id=33 --directory=client_test --temporary_state_directory=client_st ' + \
                  '--logfile=client33.log --peer_selection_mode=enable --ranking_source=geoip ' + \
                  '--neighbour_selection_mode=enable --sis_url=http://localhost:8080/sis ' + \
                  '--upload=768 --download=768 --single_torrent=startrek.torrent ' + \
                  '--report_to=http://localhost:3333 --loglevel=ERROR -e seeding 150 ' + \
                  '--I=130.83.78.43/16;130.84.1.1/16 --activity_report_interval=60'
        
        client_config = ClientConfiguration()
        client_config.update_from_cl(cmdline.split(' '))
        
        self.assertEquals(8800, client_config.get_port())
        self.assertEquals(33, client_config.get_id())
        self.assertEquals('client_test', client_config.get_directory())
        self.assertEquals('client_st', client_config.get_state_directory())
        self.assertEquals('client33.log', client_config.get_logfile())
        self.assertEquals(constants.PS_MODE_ENABLE, client_config.get_peer_selection_mode())
        self.assertEquals(constants.RS_GEOIP, client_config.get_ranking_source())
        self.assertEquals(constants.NS_MODE_ENABLE, client_config.get_ns_mode())
        self.assertEquals('http://localhost:8080/sis', client_config.get_sis_url())
        self.assertEquals('http://localhost:8080/sis/ClientEndpoint', client_config.get_sis_client_endpoint())
        self.assertEquals(768, client_config.get_upload_limit())
        self.assertEquals(768, client_config.get_download_limit())
        self.assertEquals('startrek.torrent', client_config.get_single_torrent())
        self.assertEquals('http://localhost:3333', client_config.get_report_to())
        self.assertEquals(constants.EXIT_ON_SEEDING_TIME, client_config.get_exit_on())
        self.assertEquals(150, client_config.get_seeding_time())
        self.assertEquals(60, client_config.get_activity_report_interval())
        self.assertEquals(['130.83.78.43/16','130.84.1.1/16'], client_config.get_ip_prefixes())
    
    def test_client_config_from_static_with_cl_update(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        static_conf_file = os.path.join(cwd, "test_client_static.conf")
        if not os.access(static_conf_file, os.F_OK):
            self.fail("Unable to locate test_cache_static.conf")        

        cmdline = '--config=%s' % static_conf_file
        
        client_config = ClientConfiguration()
        client_config.update_from_cl(cmdline.split(' '))
        
        self.assertEquals(constants.NS_MODE_ENABLE, client_config.get_ns_mode())
        self.assertEquals(0.8, client_config.get_locality_preference())
        self.assertEquals(constants.PS_MODE_ENABLE, client_config.get_peer_selection_mode())
        self.assertEquals(5, client_config.get_rating_cache_interval())
        self.assertEquals(316, client_config.get_download_limit())
        self.assertEquals(316, client_config.get_upload_limit())
        self.assertEquals(7, client_config.get_max_upload_slots_per_download())
        self.assertEquals(simpledefs.DLMODE_VOD, client_config.get_download_mode())
        self.assertEquals(10, client_config.get_connection_limit())
        self.assertEquals('torrents/startrek.torrent', client_config.get_single_torrent())
        self.assertEquals('xml', client_config.get_serialization_method())
        self.assertEquals(False, client_config.get_compress_xml_reports())
        self.assertEquals(1.0, client_config.get_report_interval())
        self.assertEquals(1234567, client_config.get_id())
        
#min_uploads: 4
#max_initiate: 10
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner().run(suite)