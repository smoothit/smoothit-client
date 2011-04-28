import subprocess
import os
import shutil
import time
import sys
import TestbedReader
import optparse
import tempfile
from SisClient.Testbed.Utils import profiler

from tracker import *
from subprocess import Popen
from logger import *
from SisClient.Testbed.Reporting.webserver import *
from SisClient.Testbed.Reporting import webserver 
from SisClient.Testbed.Utils.utils import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from BaseLib.Core.API import *

from TestbedConfig import TestbedConfiguration
from TestbedConfig import TestbedClientConfiguration
from TestbedConfig import TestbedTrackerConfiguration
from callback import *
from traceback import *

from SisClient.Common import constants
from SisClient.Utils.common_utils import get_exit_on_as_string

__author__ = "Markus Guenther"

class Testbed:
    '''An instance of this class runs a local testbed on multiple Python 
    processes. The instance itself encapsulates an internal tracker as well
    as a report analyzer, to which clients can report their status. The analyzer
    has a webserver frontend which is programmatically specified in module
    webserver.py of the Testbed package.
    
    A Testbed instance consumes a TestbedConfiguration object that specifies
    the parameters for the environment, such as clients along with their details,
    files that shall be distributed as well as general parameters that serve
    as a configuration for a Testbed.
    
    Testbed also keeps track of the amount of time that passed since its
    instantiation. You can use this to limit the execution time of your 
    tests.
    
    The Testbed enters its main loop by running Testbed.run(). This method
    will return the results of the tests (conditions passed, conditions failed)
    to the invoker in form of a TestbedResult object.
    '''
    def __init__(self, config):
        self.config = config
        self.startedAt = time.time()
        self.runningClients = []
        self.clientsToStart = []

    def _setup(self):
        '''Sets up the environment for the testbed. This includes the creation
        of the necessary directory structure, as well as starting tracker
        and clients.
        '''
        baseDirectory = self.config.get_base_directory()
        FileUtils.create_directory(baseDirectory, removeOld=True)
        FileUtils.create_directory(baseDirectory + "logs" + os.path.normcase('/'))
        init_logger(baseDirectory + "logs" + os.path.normcase('/') + "testbed.log")
        self._logger = logging.getLogger(self.__class__.__name__)
        
        self._logger.info("Created base directory at %s" % baseDirectory)
        self._logger.info("Created log output directory at %s" % (baseDirectory + "logs" + 
                                                                  os.path.normcase('/')))
        
        files = self.config.get_files()
        # starts another designated client which acts as the tracker
        self._logger.info("Setting up the internal tracker")
        self.tracker = TestbedExternalTracker(self.config.get_tracker())
        files = self.tracker.start_tracker(files)
        # give the tracker some time to create torrent files
        time.sleep(10)
        
        # instantiate client starter objects
        for client_config in self.config.get_clients():
            client = TestbedClient(client_config)
            self.clientsToStart.append(client)
            
        for cache_config in self.config.get_caches():
            cache = TestbedCache(cache_config)
            self.clientsToStart.append(cache)
                
    def is_running(self):
        '''Return a boolean value that determines whether the testbed execution
        has come to an end.
        '''
        return (time.time() - self.startedAt < self.config.get_timeout())
    
    def _check_for_clients_to_start(self):
        if len(self.clientsToStart) == 0:
            return
        running_time = time.time() - self.startedAt
        # check if we have to start some clients
        for client in self.clientsToStart:
            if client.get_configuration().get_birth_time() <= running_time:
                client.start(self.config.get_files()) 
                self.runningClients.append(client)
                self.clientsToStart.remove(client)
    
    def _check_for_clients_to_kill(self):
        if len(self.runningClients) == 0:
            return
        # check if we have to kill some running clients
        running_time = int(time.time() - self.startedAt)
        for client in self.runningClients:
            if client.get_configuration().get_death_time() <= running_time:
                client.kill_subprocess()
                self.runningClients.remove(client)
    
    def _kill_remaining_clients(self):
        for client in self.runningClients:
            client.kill_subprocess()
            #self.runningClients.remove(client)

    
    def run(self):
        '''Clients of Testbed should call this function to start the execution
        of the testbed after its configuration. Returns a TestbedResult object
        which contains information about the specific testbed parameters as
        well as the status of the conditions for a successful test.
        '''
        
        webserver.statistic.clean()
        webserver.statistic.set_basedir(self.config.get_base_directory())
        
        self._setup()
        self._check_for_clients_to_start()
        
        self._logger.info("Passing conditions to analyzer...")
        webserver.analyzer.clean()
        webserver.analyzer.set_conditions(self.config.get_conditions())
        try:
            serverAddress = ("localhost", 8888)
            self._logger.info("Setting up webserver at %s:%i..." % (serverAddress[0],
                                                                    serverAddress[1]))
            server = HTTPServer(serverAddress, ReportHandler)
            
            while self.is_running():
                self._check_for_clients_to_start()
                self._check_for_clients_to_kill()
                server.handle_request()
                
            self._logger.info("Timeout reached. Exiting...")
        except KeyboardInterrupt:
            print_exc()
            server.socket.close()
        finally:
            # test finished, now create a summary and print it to the user
            result = TestbedResult(self.config.get_test_name(),
                                   webserver.analyzer.get_satisfied_conditions(),
                                   webserver.analyzer.get_remaining_conditions(),
                                   time.time() - self.startedAt)
        
            # shutdown the tracker
            self._logger.info("Killing tracker with pid %i " % self.tracker.get_pid())
            self._logger.info("Returncode: %s" % self.tracker.kill_subprocess())
            # kill all clients as well
            self._logger.info("Killing remaining clients...")
            self._kill_remaining_clients()
            
            webserver.statistic.write_all()
                    
            return result
        
class ProfileableTestbed(Testbed):
    def __init__(self, config):
        Testbed.__init__(self, config)
        self._memory = []
    
    def _memory_consumption(self):
        '''Uses the Testbed.profiler module to query for the overall
           memory consumption of the Testbed at call time. The result
           is a 2-tuple (time in s, total memory consumption in bytes
           at call time) and will be stored for future reference.
        '''
        t, consumption = profiler.memory(os.getpid())
        consumption /= 1024.0*1024.0
        for client in self.runningClients:
            consumption += profiler.memory(client.get_pid())[1] / (1024.0*1024.0)
        self._memory.append((t, consumption))

    def get_memory_consumption_at_runtime(self):
        '''Returns a list of 2-tuples (time in s, total memory consumption in
           bytes).
        '''
        return self._memory
    
    def is_running(self):
        '''Return a boolean value that determines whether the testbed execution
        has come to an end. Logs a short summary of the overall memory
        consumption (Testbed including all Python processes it has started)
        in addition.
        '''
        self._memory_consumption()
        return Testbed.is_running(self)

class TestbedResult():
    '''Holds result data and presents it as a nicely formatted string.
    '''
    def __init__(self, testname, satisfied, notSatisfied, runningTime):
        self.satisfied = satisfied
        self.notSatisfied = notSatisfied
        self.runningTime = runningTime
        self.testname = testname
    
    def __str__(self):
        dispatch = "\nTEST: %s\n" % self.testname
        
        if len(self.satisfied) != 0 and len(self.notSatisfied) != 0:
            dispatch += "\tCONDITIONS SATISFIED: %i\n" % len(self.satisfied)
            for cond in self.satisfied:
                dispatch += "\t\t%s\n" % cond.__str__()
                dispatch += "\tCONDITIONS NOT SATISFIED: %i\n" % len(self.notSatisfied)
                for cond in self.notSatisfied:
                    dispatch += "\t\t%s\n" % cond.__str__()
        
                    dispatch += "PASSED RATIO: %i percent\n" % (100.0*len(self.satisfied)/
                                                                (len(self.satisfied)+len(self.notSatisfied)))
        dispatch += "TOTAL TIME: %i seconds" % self.runningTime
        return dispatch

class SubprocessInstantiator():
    '''This is the base class for all classes that need the functionality
    to open up new Python processes. Be aware of the fact that these child
    processes will get terminated upon termination of the Testbed script.
    
    Please note that for some matter the PIDs that a Popen child
    is assigned to differs by 1 from the "real" PID on a Unix system.
    This class adjusts the PID so that the subprocess can get killed
    "properly".
    '''
    def __init__(self):
        self.child = None
    
    def create_subprocess(self, cmd):
        '''Uses the Popen module to spawn a child process of the Testbed
        script.
        '''
        self.child = Popen(cmd, shell=True)
        
    def kill_subprocess(self):
        '''Finished the previously created child process. Returns immediately
           if the respective subprocess was not created before.
        '''
        if self.child is not None:
            cmd = "kill %i" % (self.child.pid+1)
            p = Popen(cmd, shell=True)
            return str(p.returncode)
        
    def get_pid(self):
        '''Returns the PID of the child. 
        '''
        if self.child is not None:
            return self.child.pid+1
        
class TestbedClient(SubprocessInstantiator):
    '''
    Consumes a TestbedClientConfiguration object which is used to parameterize
    a specific client. Because a Tribler session is a singleton, each and every
    client has to be spawned as a new subprocess to the Testbed. Hence,
    SubprocessInstantiator is the base class for this class.
    
    TestbedClient also takes care of the client's directory setup.
    '''
    def __init__(self, configuration):
        assert configuration is not None
        self.configuration = configuration
        # generate directory name
        self.directory = self.configuration.get_base_directory() + "client" + \
            str(self.configuration.get_id()) + os.path.normcase('/')
        
    def _setup_client_environment(self, files):
        FileUtils.create_directory(self.directory)
        
        # the client needs the torrents for all the files in the seeding and
        # leeching list to be stored at his download directory
        seedingList = self.configuration.get_seeding_list()
        leechingList = self.configuration.get_leeching_list()
        for fileref in remove_duplicate_elements_from_list(seedingList + leechingList):
            # search for fileref in files
            for file in files:
                if file.get_id() == fileref:
                    # found it
                    torrentDestination = self.directory + \
                        FileUtils.get_relative_filename(file.get_torrent())
                    shutil.copyfile(file.get_torrent(), torrentDestination)
                    
                    # if the client acts as a seeder, then we need to copy the full
                    # download into its download directory as well
                    if fileref in seedingList:
                        destination = self.directory + \
                            FileUtils.get_relative_filename(file.get_absolute_path_to_file())
                        shutil.copyfile(file.get_absolute_path_to_file(), destination)
                    
    def get_configuration(self):
        return self.configuration
    
    def start(self, files):
        '''Does the necessary setup for the client instance and starts it
           as a new Python process.
        '''
        self._setup_client_environment(files)
        
        clientPy = "\"" + FileUtils.get_current_script_directory(__file__) + \
                  os.path.normcase('/') + "client.py\" "
        cmd = "python " + clientPy + "--port=%i --id=%i --directory=\"%s\" --neighbour_selection_mode=%s --peer_selection_mode=%s --upload=%i --download=%i" % \
                (self.configuration.get_port(),
                 self.configuration.get_id(),
                 self.directory[:len(self.directory)-1],
                 self.configuration.get_neighbour_selection_mode(),
                 self.configuration.get_peer_selection_mode(),
                 self.configuration.get_uprate(),
                 self.configuration.get_downrate())
                
        if self.configuration.get_logfile() is not None:
            cmd += " --logfile=%s" % self.configuration.get_logfile()
        if self.configuration.get_sis_url() is not None:
            cmd += " --sis_url=%s" % self.configuration.get_sis_url()
        if self.configuration.get_config() is not None:
            cmd += " --config=%s" % self.configuration.get_config()
#        if self.configuration.get_exit_after_dl():
#            cmd += " --exit_after_dl=True"
        exit_on = self.configuration.get_exit_on()
        if exit_on == constants.EXIT_ON_SEEDING_TIME:
            cmd += " -e %s %i" % (get_exit_on_as_string(exit_on), self.configuration.get_seeding_time())
        else:
            cmd += " -e %s" % get_exit_on_as_string(exit_on)
        cmd += " --report_to=%s" % ("http://localhost:8888")
        
        logger = logging.getLogger()
        logger.debug(cmd)
        
        self.create_subprocess(cmd)

class TestbedCache(SubprocessInstantiator):
            
    def __init__(self, configuration):
        assert configuration is not None
        self.configuration = configuration
        # generate directory name
        self.directory = self.configuration.get_base_directory() + "cache" + \
            str(self.configuration.get_id()) + os.path.normcase('/')
        
    def _setup_cache_environment(self, files):
        FileUtils.create_directory(self.directory)
        
        # the cache needs the torrents for all the files in the seeding and
        # leeching list to be stored at his download directory
        seedingList = self.configuration.get_seeding_list()
        leechingList = self.configuration.get_leeching_list()
        for fileref in remove_duplicate_elements_from_list(seedingList + leechingList):
            # search for fileref in files
            for file in files:
                if file.get_id() == fileref:
                    # found it
                    torrentDestination = self.directory + \
                        FileUtils.get_relative_filename(file.get_torrent())
                    shutil.copyfile(file.get_torrent(), torrentDestination)
                    
                    # if the client acts as a seeder, then we need to copy the full
                    # download into its download directory as well
                    if fileref in seedingList:
                        destination = self.directory + \
                            FileUtils.get_relative_filename(file.get_absolute_path_to_file())
                        shutil.copyfile(file.get_absolute_path_to_file(), destination)
    
    def start(self, files):
        self._setup_cache_environment(files)
        
        cachePy = "\"" + FileUtils.get_current_script_directory(__file__) + \
                  os.path.normcase('/') + "Cache" +os.path.normcase('/') + "Cache.py\" "
        cmd = "python " + cachePy + "--port=%i --id=%i --directory=\"%s\" --torrentdir=\"%s\" --neighbour_selection_mode=%s --peer_selection_mode=%s --uplimit=%i --downlimit=%i --spacelimit=%i --conlimit=%i" % \
                (self.configuration.get_port(),
                 self.configuration.get_id(),
                 self.directory[:len(self.directory)-1],
                 self.directory[:len(self.directory)-1],
                 self.configuration.get_neighbour_selection_mode(),
                 self.configuration.get_peer_selection_mode(),
                 self.configuration.get_uprate(),
                 self.configuration.get_downrate(),
                 self.configuration.get_spacelimit(),
                 self.configuration.get_conlimit())
                
        if self.configuration.get_logfile() is not None:
            cmd += " --logfile=%s" % self.configuration.get_logfile()
        if self.configuration.get_sis_url() is not None:
            cmd += " --sis_url=%s" % self.configuration.get_sis_url()
        if self.configuration.get_config() is not None:
            cmd += " --config=%s" % self.configuration.get_config()
        cmd += " --report_to=%s" % ("http://localhost:8888")
        
        self.create_subprocess(cmd)
        
    def get_configuration(self):
        return self.configuration

class TestbedExternalTracker(SubprocessInstantiator):
    '''Consumes a TestbedTrackerConfiguration object which is used to
       parameterize a concrete tracker instance. The tracker runs in its
       own Python process.
       
       TestbedExternalTracker also takes care of the tracker's directory setup.
    '''
    def __init__(self, configuration):
        assert configuration is not None
        self.configuration = configuration
        
    def start_tracker(self, files):
        '''Does the necessary setup for the tracker instance and starts
           it as a new Python process.
        '''
        assert files is not None
        assert len(files) > 0
        # create a temporary directory that can be used to store the
        # files that will be shared within the current testbed instance
        self.tfdir = tempfile.mkdtemp()
        # tracker directory
        directory = self.configuration.get_base_directory() + "tracker" + \
            os.path.normcase('/')
        FileUtils.create_directory(directory)
        
        # copy all the given files to this directory
        for file in files:
            abs_name = file.get_absolute_path_to_file()
            rel_name = file.get_relative_filename()
            destination = self.tfdir + os.path.normcase('/') + rel_name
            shutil.copyfile(abs_name, destination)
            file.set_absolute_path_to_file(destination)
            file.set_torrent(directory + rel_name + constants.TORRENT_DOWNLOAD_EXT)        
            
        # now start the tracker as a new subprocess
        trackerPy = "\"" + FileUtils.get_current_script_directory(__file__) + \
                    os.path.normcase('/') + "tracker.py\" "
        cmd = "python " + trackerPy + "--url=%s --directory=%s --files_directory=%s" % \
            (self.configuration.get_url(),             
             #self.configuration.get_piece_length(),
             directory,
             self.tfdir)
        
        self.create_subprocess(cmd)
        
        return files
                
def run_from_external_module(moduleFile, profile=False):
    '''This method consumes a String that refers to a Python module. The
       given module will be loaded dynamically into the current Python
       execution environment. Every test function that is specified in that
       module gets called by this function, passing a newly created
       TestbedConfiguration object.
    '''
    logger = logging.getLogger("Testbed.run_from_external_module")
    logger.info("Loading test module...")
    module, tests = load_test_module(moduleFile)
            
    for test in tests:
        logger.info("Invoking %s..." % str(test))
        config = TestbedConfiguration()
        test(config)
        testbed = None
        if profile:
            testbed = ProfileableTestbed(config)
        else:
            testbed = Testbed(config)
        result = testbed.run()
        logger.info(result.__str__())
        
        if os.path.isfile("analyzer.out"):
            lop = config.get_processors()
            for processor in lop:
                processor("analyzer.out")
            os.unlink("analyzer.out")
        
        if profile:
            mem_overall = testbed.get_memory_consumption_at_runtime()
            for mem in mem_overall:
                logger.info("Memory consumption at time %s: %s (MB)" % \
                            (mem[0], mem[1]))
        
    logger.info("All tests completed.")
    sys.exit()

def run_from_external_file(file, profile=False):
    '''Reads a Testbed configuration from an external specification and
       invokes a Testbed instance, passing the parsed TestbedConfiguration
       object along.
    '''
    config =  TestbedReader.read_specification(file)
    testbed = None
    if profile:
        testbed = ProfileableTestbed(config)
    else:
        testbed = Testbed(config)
    result = testbed.run()
    logger.info(result.__str__())
        
    if profile:
        mem_overall = testbed.get_memory_consumption_at_runtime()
        for mem in mem_overall:
            logger.info("Memory consumption at time %s: %s (MB)" % \
                            (mem[0], mem[1]))
    sys.exit()

def main():
    init_logger("testbed.log")
    
    parser = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options]")
    
    parser.add_option("-m", "--module",
                      action="store", dest="module", default=None,
                      help="Specifies the test module which shall be loaded into " + \
                      "the testbed core.")
    parser.add_option("-e", "--extern",
                      action="store", dest="extern", default=None,
                      help="Specifies an external file which holds information " + \
                      "on how to setup a testbed declaratively.")
    parser.add_option("-p", "--profile",
                      action="store_true", dest="profile", default=False,
                      help="Run a memory profiler along with the Testbed.")
    
    (options, args) = parser.parse_args()
    
    if options.extern is None and options.module is None:
        parser.print_help()
        parser.error("You have to choose either a test module or a file which " + \
                     "holds a declarative description of a testbed instance.")

        sys.exit()
        
    if options.extern is not None and options.module is not None:
        parser.print_help()
        parser.error("Please choose either the module or extern parameter. " + \
                     "Both parameters will not work together.")
        sys.exit()
        
    if options.extern is not None:
        # parse the external specification and setup a testbed instance
        run_from_external_file(options.extern, options.profile)
    elif options.module is not None:
        # load the given module dynamically and invoke tests
        run_from_external_module(options.module, options.profile)

if __name__ == "__main__":
    main()
