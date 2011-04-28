import random
import os
import re

from Conditions import Condition
from SisClient.Testbed.Utils.utils import *
from SisClient.Testbed.callback import *
from SisClient.Common import constants

'''This package contains classes that shall be used to configure an 
   instance of the Testbed.
'''

DEFAULT_TIMEOUT = 300 # works for the testbed as well as for the death
                      # time of clients
                      
# TODO: Remove birth death from client config (not needed any longer)
# (mgu): Not true, since the local testbed relies on this at the moment.

class TestbedClientConfiguration:
    '''TestbedConfiguration.add_client returns an instance of this class
       with already predefined default values. Please see the interface
       of TestbedClientConfiguration and the commentary provided with the
       source code on how to change specific settings.
    '''
    def __init__(self, id, port=None, uprate=None, downrate=None, sisUrl=None,
                 peerSelection="none", neighbourSelection="none", logfile=None,
                 birth=0, death=DEFAULT_TIMEOUT, exit_on=constants.EXIT_ON_ALL_FINISHED,
                 rankingSource="none"):
        self.id = id
        # set other attributes to standard values
        self.port = port or self.get_random_port()
        self.baseDirectory = ""
        self.uprate = uprate or 32
        self.downrate = downrate or 32
        self.seeding = []
        self.leeching = []
        self.peerSelection = peerSelection
        self.neighbourSelection = neighbourSelection
        self.logfile = logfile
        self.sisUrl = sisUrl
        self.birth = birth
        self.death = death
#        self.exit_after_download = False
        self.config = None
        self.exit_on = exit_on
        self.seeding_time = 0
        self.ranking_source = rankingSource
        
    def set_exit_on(self, exit_on):
        assert exit_on in constants.EXIT_ON_LIST
        self.exit_on = exit_on
            
    def get_exit_on(self):
        return self.exit_on
    
    def get_seeding_time(self):
        return self.seeding_time
    
    def set_seeding_time(self, seeding_time):
        self.seeding_time = seeding_time
        
    def set_birth_time(self, birth):
        '''Sets the time of birth for the client.
        '''
        assert birth >= 0
        self.birth = birth
        
    def get_birth_time(self):
        '''Returns the birth time for the client.
        '''
        return self.birth
        
    def set_death_time(self, death):
        '''Sets the time of death for the client.
        '''
        assert death >= 0
        assert death > self.birth
        self.death = death
        
    def get_death_time(self):
        '''Returns the death time for the client.
        '''
        return self.death
        
    def set_sis_url(self, sisUrl):
        '''Configures the URI at which the SIS server can be reached.
        '''
        self.sisUrl = sisUrl
        
    def get_sis_url(self):
        '''Returns the URI at which the SIS server can be reached.
        '''
        return self.sisUrl
        
    def set_id(self, id):
        '''Configures the client id. The testbed will not check if every
           client has an unique id. Clients should assure that given ids
           are unique for a testbed run - for reasons of clarity.
        '''
        self.id = id
    
    def get_id(self):
        '''Returns the client id.
        '''
        return self.id
    
    def set_port(self, port):
        '''Configures the client's port number. Although it is possible on
           Windows systems to run programs on a port below the magic number
           1000, the testbed will prohibit this simply because of compatibility
           issues with other operating systems.
           
           Throws an assertion error if a port number < 1000 is passed as an
           argument.
        '''
        assert port > 1000
        self.port = port
        
    def get_port(self):
        '''Returns the port number.
        '''
        return self.port
    
    def set_uprate(self, uprate):
        '''Configures the upload rate in KB/s for the client.
        
           Throws an assertion error if an upload rate < 0 is passed as an
           argument.
        '''
        assert uprate >= 0
        self.uprate = uprate
        
    def get_uprate(self):
        '''Returns the upload rate in KB/s for the client.
        '''
        return self.uprate
    
    def set_downrate(self, downrate):
        '''Configures the download rate in KB/s for the client.
        
           Throws an assertion error if a download rate < 0 is passed as
           an argument.
        '''
        assert downrate >= 0
        self.downrate = downrate
        
    def get_downrate(self):
        '''Returns the download rate in KB/s for the client.
        '''
        return self.downrate
    
    def set_base_directory(self, baseDirectory):
        '''Configures the base directory for the client. This is usually
           the same as for the testbed instance itself as well as for all
           other clients that run in the same testbed instance.
           TestbedConfiguration sets this attribute to its proper
           value, so there is no need for a client to set this value
           by its own unless you explicitly want a different base directory.
        '''
        if baseDirectory is "":
            baseDirectory = "./"
        if not baseDirectory.endswith(os.path.normcase('/')):
            baseDirectory += os.path.normcase('/')
            
        self.baseDirectory = baseDirectory
        
    def get_base_directory(self):
        '''Returns the base directory for that client. This value is set
           upon initialization. TestbedConfiguration assures that this
           value will be set properly if you create an object instance of 
           this class via TestbedConfiguration.add_client.
        '''
        return self.baseDirectory
    
    def add_file_to_leech(self, fileId):
        '''Adds the file id of a file that the client shall leech during
           the testbed run. Note that if you pass the same id to
           add_file_to_leech and to add_file_to_seed your testbed instance
           might not run the way it was supposed to be.
        '''
        self.leeching.append(fileId)
    
    def get_leeching_list(self):
        '''Returns the list of all files that the client shall leech during
           the testbed run.
        '''
        return self.leeching
        
    def add_file_to_seed(self, fileId):
        '''Adds the file id of a file that the client shall seed during the
           testbed run. Note that if you pass the same id to
           add_file_to_leech and to add_file_to_seed your testbed instance
           might not run the way it was supposed to be.
        '''
        self.seeding.append(fileId)
        
    def get_seeding_list(self):
        '''Returns the list of all files that the client shall seed during
           testbed run.
        '''
        return self.seeding
    
    def set_peer_selection_mode(self, mode):
        '''Configures the peer selection mode for the client. Admissible
           values for this mode are: none, enable.
           
           Throws an assertion error if the given mode is not among the
           admissible modes.
        '''
        assert mode in ["none", "enable"]
        self.peerSelection = mode
    
    def get_peer_selection_mode(self):
        '''Returns the peer selection mode for this client configuration.
        '''
        return self.peerSelection
    
    def set_neighbour_selection_mode(self, mode):
        '''Configures the neighbour selection mode for the client.
           Admissible values for this mode are: none, enable.
           
           Throws an assertion error if the given mode is not among the
           admissible modes.
        '''
        assert mode in ["none", "enable"]
        self.neighbourSelection = mode
        
    def get_neighbour_selection_mode(self):
        '''Returns the neighbour selection mode for this client configuration.
        '''
        return self.neighbourSelection
    
    def set_ranking_source(self, ranking_source):
        assert ranking_source in ["none", "samehost", "geoip", "odd_even", "sis", "sis_simple, ip_pre"]
        self.ranking_source = ranking_source
    
    def get_ranking_source(self):
        return self.ranking_source
    
    def set_logfile(self, logfile):
        '''Configures the logfile for the client. logfile can point to
           an existing or non-existing file on your local file system.
           The path to this file should already exist on your file system,
           so the safest way to use this is to simple put it into the
           base directory of your testbed instance.
        '''
        self.logfile = logfile
        
    def get_logfile(self):
        '''Returns a string value that represents the location of the
           logfile. Returns None if this value was not previously set.
        '''
        return self.logfile
        
    def get_random_port(self):
        '''Returns a random port in the range of PORT_RANGE_LOWER_BOUND
           to PORT_RANGE_UPPER_BOUND.
        '''
        return random.randint(constants.PORT_RANGE_LOWER_BOUND, 
                              constants.PORT_RANGE_UPPER_BOUND)
    
    def set_config(self, config):
        ''' Sets the path of the config file.
        '''
        self.config = config
    
    def get_config(self):
        ''' Returns the path of the config file
        '''    
        return self.config
    
class TestbedCacheConfiguration(TestbedClientConfiguration):
    
    def __init__(self, id, port=None, uprate=None, downrate=None, sisUrl=None,
                 peerSelection="none", neighbourSelection="none", logfile=None,
                 spacelimit=800, conlimit=200):
        
        TestbedClientConfiguration.__init__(self, id, port, uprate, downrate, sisUrl, peerSelection, neighbourSelection, logfile)
        self.spacelimit = spacelimit
        self.conlimit = conlimit
    
    def set_conlimit(self, conlimit):
        ''' Sets the global connection limit of the cache.
        '''
        self.conlimit = conlimit
    
    def get_conlimit(self):
        ''' Returns the global connection limit of the cache.
        '''
        return self.conlimit
        
    def set_spacelimit(self, spacelimit):
        ''' Sets the space limit of the cache.
        '''
        self.spacelimit = spacelimit
    
    def get_spacelimit(self):
        ''' Returns the space limit of the cache.
        '''
        return self.spacelimit
        
class TestbedTrackerConfiguration():
    '''TestbedConfiguration.add_tracker returns an instance of this class
       with already predefined default values. It is used to specify
       the parameters for an internal tracker that the later Testbed
       will use to track files. Please see the interface of
       TestbedTrackerConfiguration and the commentary provided with the
       source code on how to change specific settings.
    '''
    def __init__(self, uprate=None, downrate=None, url=None, pieceLength=None):
        # assign default values
        self.baseDirectory = None
        self.uprate = uprate or 32
        self.downrate = downrate or 32
        if url is not None and not verify_tracker_url(url) or \
            url is None:
            self.url = "http://localhost:8859/announce"
        else:
            self.url = url
        self.pieceLength = pieceLength or 32768
        
    def set_uprate(self, uprate):
        '''Configures the upload rate in KB/s for the tracker.
        
           Throws an assertion error if an upload rate < 0 is passed as an
           argument.
        '''
        assert uprate >= 0
        self.uprate = uprate
        
    def get_uprate(self):
        '''Returns the upload rate in KB/s for the tracker.
        '''
        return self.uprate
    
    def set_downrate(self, downrate):
        '''Configures the download rate in KB/s for the tracker.
        
           Throws an assertion error if a download rate < 0 is passed as
           an argument.
        '''
        assert downrate >= 0
        self.downrate = downrate
        
    def get_downrate(self):
        '''Returns the download rate in KB/s for the tracker.
        '''
        return self.downrate    
    
    def set_base_directory(self, baseDirectory):
        '''Configures the base directory for the client. This is usually
           the same as for the testbed instance itself as well as for all
           other clients that run in the same testbed instance.
           TestbedConfiguration sets this attribute to its proper
           value, so there is no need for a client to set this value
           by its own unless you explicitly want a different base directory.
        '''
        if baseDirectory is "":
            baseDirectory = "./"
        if not baseDirectory.endswith(os.path.normcase('/')):
            baseDirectory += os.path.normcase('/')
            
        self.baseDirectory = baseDirectory
        
    def get_base_directory(self):
        '''Returns the base directory for the tracker.
        '''
        return self.baseDirectory
    
    def set_url(self, url):
        '''Configures the URI at which the tracker can be reached by clients.
        If the passed url does not follow the pattern http://your-url:port/announce,
        the url parameter of the testbed tracker will not be changed. Throws
        an assertion error if the included port number is <= 1024.
        '''
        if not verify_tracker_url(url):
            return
        port = int(extract_tracker_port_from_url(url))
        assert port > 1024
        
        self.url = url
        
    def get_url(self):
        '''Returns the URI for the tracker. If not previously set, this
           returns the default value "http://localhost:8859/announce", because
           the Testbed runs only on local machines currently.
        '''
        return self.url
    
    def set_piece_length(self, pieceLength):
        '''Configures the piece length. This parameter is used for the creation
           of torrent files.
           
           Throws an assertion error if the given parameter is < 1.
        '''
        assert pieceLength > 0
        self.pieceLength = pieceLength
        
    def get_piece_length(self):
        '''Returns the specified piece length. This defaults to 32768 if not
           previously set by the client.
        '''
        return self.pieceLength
    
class TestbedFile():
    '''TestbedConfiguration.add_file returns an instance of this class.
       Please see the interface of TestbedFile and the commentary provided with 
       the source code on how to change specific settings.
    '''
    def __init__(self, id, absolutePathToFile):
        self.id = id
        self.absolutePathToFile = absolutePathToFile
        self.torrent = None
        
    def set_id(self, id):
        '''Sets the id of the file configuration. This id is used by
           client configurations to address files in their leeching
           and seeding lists. This value should be unique for a testbed
           instance.
        '''
        self.id = id

    def get_id(self):
        '''Returns the specified id for this file configuration.
        '''
        return self.id
    
    def set_absolute_path_to_file(self, absolutePathToFile):
        '''Configures the absolute path to the file you want to distribute
           within a testbed instance.
        '''
        self.absolutePathToFile = absolutePathToFile
    
    def get_absolute_path_to_file(self):
        '''Returns the absolute path to the file.
        '''
        return self.absolutePathToFile
    
    def get_relative_filename(self):
        '''Returns the relative filename of the file specified by the
           absolutePathToFile attribute.
        '''
        return FileUtils.get_relative_filename(self.absolutePathToFile)
    
    def set_torrent(self, torrent):
        '''Configures the location of the torrent to the file. Usually,
           that torrent file does not exist and will be created later
           by the internal tracker of a testbed instance. The tracker
           will set this attribute properly.
        '''
        self.torrent = torrent
        
    def get_torrent(self):
        '''Returns the torrent for the file.
        '''
        return self.torrent
    
class TestbedConfiguration():
    '''This is the main class to operate with if you want to specify a
       testbed configuration. Every user-supplied test code gets a fresh
       instance of this class passed. The client can then specify the
       parameters of the test by using the interface of TestbedConfiguration.
    '''
    def __init__(self, baseDirectory="", sisUrl=None, testName=None):
        self.set_base_directory(baseDirectory)
        self.set_sis_url(sisUrl)
        self.testName = testName or "Custom test"
        self.timeout = 300 # in seconds
        self.tracker = None
        self.sisUrl = sisUrl
        self.clients = []
        self.caches = []
        self.files = []
        self.conditions = []
        self.processors = []
        
    def get_conditions(self):
        '''Returns a list of all conditions that were previously added to
           the testbed configuration.
        '''
        return self.conditions
    
    def get_files(self):
        '''Returns a list of all files that were previously added to
           the testbed configuration. 
        '''
        return self.files
    
    def get_clients(self):
        '''Returns a list of all clients that were previously added to
           the testbed configuration.
        '''
        return self.clients
    
    def get_caches(self):
        '''Returns a list of all caches that were previously added to
           the testbed configuration.
        '''
        return self.caches
    
    def get_processors(self):
        '''Returns the list of processor functions that were previously
           registered at the testbed configuration.
        '''
        return self.processors
    
    def get_tracker(self):
        '''Returns the tracker configuration. Returns NoneType if the tracker
           was not configured yet.
        '''
        return self.tracker
    
    def set_base_directory(self, baseDirectory, propagate=False):
        '''Configures the base directory for the testbed. This value will
           be propagated as a default value to any client and tracker that will
           be added to this testbed configuration.
           
           The propagate parameter specifies if the given attribute for
           the base directory shall be propagated to all known clients and
           the tracker.
        '''
        if baseDirectory is "":
            baseDirectory = "./"
        if not baseDirectory.endswith(os.path.normcase('/')):
            baseDirectory += os.path.normcase('/')
            
        self.baseDirectory = baseDirectory
        
        if propagate:
            for client in self.clients:
                client.set_base_directory(baseDirectory)
            if self.tracker is not None:
                self.tracker.set_base_directory(baseDirectory)
        
    def get_base_directory(self):
        '''Returns the base directory for the testbed configuration.
        '''
        return self.baseDirectory
    
    def set_test_name(self, testName):
        '''Sets the name of the testbed instance.
        '''
        self.testName = testName
        
    def get_test_name(self):
        '''Returns the name of the testbed instance.
        '''
        return self.testName
    
    def set_timeout(self, timeout):
        '''Configures the timeout in seconds for the testbed. The testbed will
           run as long as the timeout and then exit.
        '''
        self.timeout = timeout
        
    def get_timeout(self):
        '''Returns the timeout in seconds. If not changed by user-supplied
           code, the timeout defaults to 300 seconds.
        '''
        return self.timeout
    
    def set_sis_url(self, sisUrl, propagate=False):
        '''Configures the URI at which the SIS server can be reached.
        
           The propagate parameter specifies if the given attribute for
           the SIS URI shall be propagated to all known clients.
        '''
        self.sisUrl = sisUrl
        
        if propagate:
            for client in self.clients:
                client.set_sis_url(sisUrl)
        
    def get_sis_url(self):
        '''Returns the URI at which the SIS server can be reached.
        '''
        return self.sisUrl
    
    def add_client(self, id):
        '''Creates a new client, sets its base directory equal to the
           one that is specified for the testbed and returns the newly
           created TestbedClientConfiguration object.
        '''
        client = TestbedClientConfiguration(id)
        client.set_base_directory(self.get_base_directory())
        self.clients.append(client)
        return client
    
    def add_cache(self, id):
        '''Creates a new cache, sets its base directory equal to the
           one that is specified for the testbed and returns the newly
           created TestbedCacheConfiguration object.
        '''
        cache = TestbedCacheConfiguration(id)
        cache.set_base_directory(self.get_base_directory())
        self.caches.append(cache)
        return cache
    
    def add_file(self, id, absolutePathToFile):
        '''Creates a new TestbedFile object and returns it.
        '''
        file = TestbedFile(id, absolutePathToFile)
        self.files.append(file)
        return file
    
    def add_condition(self, condition):
        '''Adds the given condition to the testbed configuration.
        
           Throws an assertion error if a parameter is passed which is not
           derived from the base class Condition.
        '''
        assert isinstance(condition, Condition)
        self.conditions.append(condition)
        
    def register_processor(self, method):
        '''Adds the given postprocessor to the testbed configuration.
           
           Throws an assertion error if a parameter is passed which is not
           derived from the base class Postprocessor.
        '''
        self.processors.append(method)
        
    def add_tracker(self):
        '''Creates a new TestbedTrackerConfiguration object, sets the
           base directory to a default value and returns the object.
        '''
        self.tracker = TestbedTrackerConfiguration()
        self.tracker.set_base_directory(self.get_base_directory())
        return self.tracker
