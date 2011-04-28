import unittest
import os

from SisClient.Testbed.Distributed import dist_config_parser
from SisClient.Testbed.Distributed.dtestbed_config import DistributedTestbedConfig
from SisClient.Testbed.Distributed.dtestbed_config import DistributedDeployment
from SisClient.Testbed.Distributed.dtestbed_config import DistributedTrackerConfiguration
from SisClient.Testbed.Utils import utils

class DistConfigParserTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest("testDistributedTest1")
        suite.addTest("testMultipleHostsPerDeployment")
        
    def testMultipleHostsPerDeployment(self):
        path = utils.FileUtils.get_current_script_directory(__file__)
        path += os.path.normcase('/') + "multiple_hosts_deployment.config"
        if not os.access(path, os.F_OK):
            # fail this test if the required file is not present in the file
            # system
            self.fail("Required file multiple_hosts_deployment.config not found at %s" % path)
        dtestbed = dist_config_parser.parse_distributed_configuration(path)

        # test hosts
        hosts = dtestbed.get_hosts()
        expected_host_keys = ["glab162", "glab163"]
        for host in hosts.keys():
            self.assertTrue(host in expected_host_keys)
        self.assertEquals("glab162.g-lab.tu-darmstadt.de", hosts["glab162"])
        self.assertEquals("glab163.g-lab.tu-darmstadt.de", hosts["glab163"])
        
        # test deployment 1 + 2
        self.assertEquals(2, len(dtestbed.get_deployments()))
        dpl0 = dtestbed.get_deployment_by_name("deployment_1")
        dpl1 = dtestbed.get_deployment_by_name("deployment_2")
        self.assertEquals(2, len(dpl0.get_hostlist()))
        self.assertEquals(2, len(dpl1.get_hostlist()))
        self.assertTrue("glab162.g-lab.tu-darmstadt.de" in dpl0.get_hostlist())
        self.assertTrue("glab163.g-lab.tu-darmstadt.de" in dpl0.get_hostlist())
        self.assertTrue("glab162.g-lab.tu-darmstadt.de" in dpl1.get_hostlist())
        self.assertTrue("glab163.g-lab.tu-darmstadt.de" in dpl1.get_hostlist())
        self.assertEquals(dpl0.get_client_conf_schema(), dpl1.get_client_conf_schema())
        self.assertEquals("/home/tud_p2p/testbed/", dpl0.get_remote_base_directory())
        self.assertEquals("/home/tud_p2p/testbed/", dpl1.get_remote_base_directory())
    
    def testDistributedTest1(self):
        path = utils.FileUtils.get_current_script_directory(__file__)
        path += os.path.normcase('/') + "sample_distributed_test1.txt"
        if not os.access(path, os.F_OK):
            # fail this test if the required file is not present in the file
            # system
            self.fail("Required file sample_distributed_test1.txt not found at %s" % path)
        dtestbed = dist_config_parser.parse_distributed_configuration(path)

        # test tracker attributes
        tracker = dtestbed.get_tracker()
        self.assertTrue(isinstance(tracker, DistributedTrackerConfiguration))
        self.assertEquals("glab162", tracker.get_hostname())
        self.assertEquals(1024, tracker.get_uprate())
        self.assertEquals(1024, tracker.get_downrate())
        self.assertEquals("/home/tud_p2p/testbed/", tracker.get_base_directory())
        self.assertEquals(30, tracker.get_waiting_time())
        tracker_files = tracker.get_files()
        expected_files = ["file1", "file2"]
        for file in tracker_files:
            self.assertTrue(file in expected_files)
            
        # test file attributes
        files = dtestbed.get_files()
        for file in files.keys():
            self.assertTrue(file in expected_files)
        file1 = files["file1"]
        file2 = files["file2"]
        self.assertEquals("file1", file1.get_id())
        self.assertEquals("client.sh", file1.get_relative_filename())
        self.assertEquals("file2", file2.get_id())
        self.assertEquals("tracker.sh", file2.get_relative_filename())
        
        # test hosts
        hosts = dtestbed.get_hosts()
        expected_host_keys = ["glab162", "glab163"]
        for host in hosts.keys():
            self.assertTrue(host in expected_host_keys)
        self.assertEquals("glab162.g-lab.tu-darmstadt.de", hosts["glab162"])
        self.assertEquals("glab163.g-lab.tu-darmstadt.de", hosts["glab163"])
        
        # test deployment 1 + 2
        self.assertEquals(2, len(dtestbed.get_deployments()))
        dpl0 = dtestbed.get_deployment_by_name("deployment_1")
        dpl1 = dtestbed.get_deployment_by_name("deployment_2")
        self.assertTrue("glab162.g-lab.tu-darmstadt.de" in dpl0.get_hostlist())
        self.assertTrue("glab163.g-lab.tu-darmstadt.de" in dpl1.get_hostlist())
        self.assertEquals(dpl0.get_client_conf_schema(), dpl1.get_client_conf_schema())
        self.assertEquals("/home/tud_p2p/testbed/", dpl0.get_remote_base_directory())
        self.assertEquals("/home/tud_p2p/testbed/", dpl1.get_remote_base_directory())

        # test schema 1
        schema1 = dpl0.get_client_conf_schema()
        self.assertEquals(128, schema1.get_uprate())
        self.assertEquals(128, schema1.get_downrate())
        leeching = schema1.get_leeching_list()
        seeding = schema1.get_seeding_list()
        self.assertTrue(len(leeching) == 1)
        self.assertTrue(len(seeding) == 1)
        self.assertEquals("file1", leeching[0])
        self.assertEquals("file2", seeding[0])
        self.assertEquals("none", schema1.get_ranking_source())
        
        # general tests
        self.assertEquals(300, dtestbed.get_timeout())
        self.assertEquals(True, dtestbed.remove_remote_files())
        self.assertEquals("dtestbed_logfiles", dtestbed.get_logfile_directory())
        # check the linearization of events
        events = dtestbed.get_events()
        self.assertEquals(2, len(events))
        self.assertEquals((0, 0, 'deployment_1'), events[0])
        self.assertEquals((30, 1, 'deployment_2'), events[1])
    
if __name__ == "__main__":
    unittest.main()