import os

from SisClient.Testbed.TestbedConfig import TestbedTrackerConfiguration
from SisClient.Testbed.TestbedConfig import TestbedFile

class DistributedTestbedConfig():
    def __init__(self):
        self._hosts = {}
        self._files = {}
        self._deployment = {}
        self._events = []
        self._tracker = None
        self._timeout = 300 # standard timeout value
        self._logfile_directory = "dtestbed_logfiles"
        self._remove_remote_files = True
        
    def set_remove_remote_files(self, remove):
        self._remove_remote_files = remove
        
    def remove_remote_files(self):
        return self._remove_remote_files
        
    def set_logfile_directory(self, logfile_directory):
        self._logfile_directory = logfile_directory
    
    def get_logfile_directory(self):
        return self._logfile_directory
        
    def set_events(self, events):
        self._events = events
        
    def get_events(self):
        return self._events
        
    def resolve_file_ref(self, file_ref):
        if file_ref not in self._files.keys():
            return None
        return self._files[file_ref].get_absolute_path_to_file()
        
    def set_timeout(self, timeout):
        assert timeout >= 0
        self._timeout = timeout
        
    def get_timeout(self):
        return self._timeout
        
    def set_tracker(self, tracker):
        assert isinstance(tracker, DistributedTrackerConfiguration)
        self._tracker = tracker
        
    def get_tracker(self):
        return self._tracker
    
    def add_host(self, host_key, host_name):
        self._hosts[host_key] = host_name
        
    def get_hosts(self):
        return self._hosts
    
    def add_file(self, file_key, file_name):
        self._files[file_key] = TestbedFile(file_key, file_name)
        
    def get_files(self):
        return self._files
    
    def add_deployment(self, name, deployment):
        assert deployment is not None
        self._deployment[name] = deployment
        
    def get_deployments(self):
        return self._deployment
    
    def get_deployment_by_name(self, name):
        if name not in self._deployment.keys():
            return None
        return self._deployment[name]
    
#    def get_deployment_for_host(self, host_key):
#        return_value = None
#        #if host_key in self._hosts.keys() and host_key in self._deployment.keys():
#        if host_key in self._deployment.keys():
#            return_value = self._deployment[host_key]
#        return return_value
    
class DistributedDeployment():
    def __init__(self, client_conf_schema, hostlist, remote_dir):
        self.client_conf_schema = client_conf_schema
        self.hostlist = hostlist
        self.remote_base_directory = remote_dir
        if not self.remote_base_directory.endswith(os.path.normcase('/')):
            self.remote_base_directory += os.path.normcase('/')
        
    def get_remote_base_directory(self):
        return self.remote_base_directory
        
    def get_client_conf_schema(self):
        return self.client_conf_schema
    
    def get_hostlist(self):
        return self.hostlist
    
class DistributedTrackerConfiguration(TestbedTrackerConfiguration):
    def __init__(self, uprate=None, downrate=None, url=None, pieceLength=None,
                 hostname = None):
        TestbedTrackerConfiguration.__init__(self, uprate, downrate, url, pieceLength)
        self._hostname = hostname
        self._files = []
        self._waiting_time = 30
        
    def set_hostname(self, hostname):
        assert hostname is not None
        self._hostname = hostname
        
    def get_hostname(self):
        return self._hostname
    
    def add_file(self, file_id):
        self._files.append(file_id)
        
    def get_files(self):
        return self._files
    
    def set_waiting_time(self, waiting_time):
        assert waiting_time >= 0
        self._waiting_time = waiting_time
        
    def get_waiting_time(self):
        return self._waiting_time