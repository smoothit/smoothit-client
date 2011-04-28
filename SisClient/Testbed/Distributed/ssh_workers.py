import paramiko
import logging
import threading
import time

from SisClient.Common import constants
from SisClient.Testbed.Utils.utils import *
from SisClient.Utils.common_utils import get_exit_on_as_string

#_______________________________________________________________________________
# ABSTRACT BASE CLASSES

class SSHWorker(threading.Thread):
    '''This class is the base class for concrete SSH workers. It provides
    abstractions for setting up a SSH connection, executing remote commands
    and disconnecting the connection. It is derived from threading.Thread,
    which enables the parallel execution of many workers.
    '''
    def __init__(self, hostname, username="", password=""):
        threading.Thread.__init__(self)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._hostname = hostname
        self._username = username
        self._password = password
        self._conn = None
        
    def _connect(self):
        '''Establishes a secure connection to the specified remote host.
        Uses Paramiko's AutoAddPolicy so that the user is not requested
        to add an unknown remote host to its known hosts.
            
        Return:
            NoneType
        '''
        if self._conn is not None:
            return
        self._conn = paramiko.SSHClient()
        self._conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._conn.connect(self._hostname,
                           username=self._username,
                           password=self._password)
        
    def _disconnect(self):
        '''Terminates a previously established secure connection.

        Return:
            NoneType
        '''
        if self._conn is None:
            return
        self._conn.close()
        
    def _run_cmd(self, cmd):
        '''Runs a command on the connected remote host, if a connection
        was previously set up.
        
        Parameter:
            cmd -- String value which represents the command that shall be
                   executed on the remote host.
        
        Return:
            NoneType
        '''
        if self._conn is None:
            self._logger.debug("Connection not established")
            return
        self._logger.debug("%s: %s" % (self._hostname, cmd))
        self._conn.exec_command(cmd)
        
    def run(self):
        '''Implementing classes must override this method and invoke the
        concrete SSH worker with SSHWorker.start(), in order to fork/start
        the thread correctly.
        
        Return:
            NoneType
        '''
        pass
    
#_______________________________________________________________________________
# CLASSES

class SSHExecuteCommandWorker(SSHWorker):
    '''Very simple class that enables the execution of a single command
    on a remote host.
    '''
    def __init__(self, hostname, cmd, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        self._cmd = cmd
        
    def run(self):
        '''Connects to the specified host, executes the command and
        disconnects immediately.
        
        Return:
            NoneType
        '''
        self._connect()
        self._run_cmd(self._cmd)
        time.sleep(1)
        self._disconnect()
    
class SSHRunTrackerWorker(SSHWorker):
    '''Starts a remote tracker.'''
    def __init__(self, hostname, configuration, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        self._configuration = configuration
        
    def run(self):
        '''Connects to the specified host, sets up the tracker and
        disconnects immediately afterwards.
        
        Return:
            NoneType
        '''
        self._connect()
        self._setup_tracker()
        self._disconnect()
        
    def _setup_tracker(self):
        '''Creates the necessary directories, copies files to 
        their supposed location and starts the tracker afterwards.
        
        Return:
            NoneType
        '''
        tracker = self._configuration.get_tracker()
        base_dir = tracker.get_base_directory()
        files = tracker.get_files()
        remote_tracker_dir = "%stracker" % base_dir
        remote_files_dir = "%stracker/files" % base_dir
        remote_logfile = "%stracker/tracker.log" % base_dir
        tracker_url = "http://%s:8859/announce" % self._hostname
        self._logger.info("Creating tracker directories...")
        self._run_cmd("mkdir %s" % base_dir)
        self._run_cmd("mkdir %s" % remote_tracker_dir)
        self._run_cmd("mkdir %s" % remote_files_dir)
        for file in files:
            filename = self._configuration.get_files()[file].get_relative_filename()
            self._run_cmd("cp %s %s" % (filename, remote_files_dir))
        
        # now start the tracker
        run_tracker_cmd = "cd tribler; sh tracker.sh -f %s -d %s -l %s -u %s" % \
                      (remote_files_dir,
                       remote_tracker_dir,
                       remote_logfile,
                       tracker_url)
        self._logger.info("Starting tracker: %s" % run_tracker_cmd)
        self._run_cmd(run_tracker_cmd)
        
class SSHRunClientWorker(SSHWorker):
    '''Starts a remote client.'''
    def __init__(self, event, configuration, hostname, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        self.event = event
        self.configuration = configuration
        
    def run(self):
        '''Connects to the specified host, creates the necessary directory
        structure for the client, copies relevant files to the client's
        directory and starts it afterwards. Terminates the connection
        after the client was started.
        
        Return:
            NoneType
        '''
        self._connect()
        self._create_directory_structure()
        self._copy_files_to_client_dir()
        self._start_client()
        self._disconnect()
        
    def _create_directory_structure(self):
        '''Creates the necessary directory structure for the client.'''
        evt_time, evt_client, evt_dpl = self.event
        dpl = self.configuration.get_deployment_by_name(evt_dpl)
        base_dir = dpl.get_remote_base_directory()
        client_dir = "%sclient%i" % (base_dir, evt_client)
        client_dl_dir = "%sclient%i/download" % (base_dir, evt_client)
        client_st_dir = "%sclient%i/state" % (base_dir, evt_client)
        self._run_cmd("mkdir %s" % base_dir)
        self._run_cmd("mkdir %s" % client_dir)
        self._run_cmd("mkdir %s" % client_dl_dir)
        self._run_cmd("mkdir %s" % client_st_dir)
        self._logger.info("Dirs: %s, %s, %s" % (client_dir, client_dl_dir, client_st_dir))
        
    def _copy_files_to_client_dir(self):
        '''Copies required files (torrent files and/or full downloads) to
        their appropriate location in the clients directory structure.
        
        Return:
            NoneType
        '''
        evt_time, evt_client, evt_dpl = self.event
        dpl = self.configuration.get_deployment_by_name(evt_dpl)
        base_dir = dpl.get_remote_base_directory()
        schema = dpl.get_client_conf_schema()
        leech = schema.get_leeching_list()
        seed = schema.get_seeding_list()
        
        #  copy torrents for leeching role
        for file in schema.get_leeching_list():
            filename = self.configuration.get_files()[file].get_relative_filename()
            torrent = filename + constants.TORRENT_DOWNLOAD_EXT
            self._run_cmd("cp %s %sclient%i/download" % (torrent, base_dir, evt_client))
        # copy torrents and full downloads for seeding role
        for file in schema.get_seeding_list():
            filename = self.configuration.get_files()[file].get_relative_filename()
            torrent = filename + constants.TORRENT_DOWNLOAD_EXT
            self._run_cmd("cp %s %sclient%i/download" % (filename, base_dir, evt_client))
            self._run_cmd("cp %s %sclient%i/download" % (torrent, base_dir, evt_client))

    def _start_client(self):
        '''Starts the client. After the start command is dispatched, the thread
        has to sleep for a short amount of time, so that the Paramiko channel
        for the command dispatch does not close immediately. This is required,
        since the way Paramiko was meant to be used inclines that after one
        dispatches a command to a remote host, he reads the lines from stdout.
        This - however - would block the execution of this method, since the
        remote client writes data to stdout as long as it runs. The time.sleep()
        approach is only a quick hack to deal with this problem.
        
        Return:
            NoneType
        '''
        evt_time, evt_client, evt_dpl = self.event
        dpl = self.configuration.get_deployment_by_name(evt_dpl)
        base_dir = dpl.get_remote_base_directory()
        client_dl_dir = "%sclient%i/download" % (base_dir, evt_client)
        client_logfile = "%sclient%i/client%i.log" % (base_dir, evt_client, evt_client)
        
        c_run_cmd = "cd tribler; sh client.sh -i %i -l %s -d %s" % \
                    (evt_client, client_logfile, client_dl_dir)
        schema = dpl.get_client_conf_schema()
        exit_on = schema.get_exit_on()
        if exit_on == constants.EXIT_ON_SEEDING_TIME:
            c_run_cmd += " -e %s %i" % (get_exit_on_as_string(exit_on), schema.get_seeding_time())
        else:
            # works for both EXIT_ON_PLAYBACK_DONE and EXIT_ON_ALL_FINISHED
            c_run_cmd += " -e %s" % get_exit_on_as_string(exit_on)
        
        self._logger.info("Starting client %i on %s" % (evt_client, self._hostname))
        self._logger.info(c_run_cmd)
        self._run_cmd(c_run_cmd)
        time.sleep(0.4)
        
class SSHKillTrackerWorker(SSHWorker):
    '''Kills the remote process of a given tracker.'''
    
    _cmd_grep_tracker_pid = "ps -AF | grep tracker.py"
    _cmd_kill_pid = "sudo kill -9 %i"
    
    def __init__(self, hostname, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        
    def run(self):
        '''Connects to the specified host, greps the tracker's PID, kills
        the corresponding process and terminates the connection immediately
        afterwards.
        
        Return:
            NoneType
        '''
        self._connect()
        stdin, stdout, stderr = self._conn.exec_command(self._cmd_grep_tracker_pid)
        for pid in stdout.read().splitlines():
            pid_number = _parse_grep_response(pid)
            if pid_number is None:
                continue
            self._logger.info("Killing tracker with pid %s on %s" % (str(pid_number), self._hostname))
            self._conn.exec_command(self._cmd_kill_pid % pid_number)
        time.sleep(1)
        self._disconnect()
        
class SSHKillAllWorker(SSHWorker):
    '''Kills everything that is alive on a given host! :)'''
    
    _cmd_grep_pcap_pid = "ps -AF | grep pcap"
    _cmd_grep_client_pid = "ps -AF | grep \"client.py\""
    _cmd_kill_pid = "sudo kill -9 %i"
    
    def __init__(self, hostname, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        
    def _kill_via_cmd(self, cmd):
        '''Kills processes by their PID. The PID are obtained by executing
        the given command. This yields a list of running processes, which is
        then parsed in order to fetch appropriate PIDs.
        
        Parameter:
            cmd -- Command that will be executed remotely to obtain a list
                   of running processes.
        
        Return:
            NoneType
        '''
        stdin, stdout, stderr = self._conn.exec_command(cmd)
        pidlines = stdout.read()
        for pid in pidlines.splitlines():
            pid_number = _parse_grep_response(pid)
            if pid_number is None:
                continue
            self._logger.info("Killing process with pid %s on %s" % (str(pid_number), self._hostname))
            self._conn.exec_command(self._cmd_kill_pid % pid_number)
        time.sleep(1)
        
    def run(self):
        '''Connects to the given host, executes kill commands for the packet
        capture software and all remaining Tribler clients and terminates
        the connection immediately afterwards.
        
        Return:
            NoneType
        '''
        self._connect()
        self._kill_via_cmd(self._cmd_grep_client_pid)
        self._kill_via_cmd(self._cmd_grep_pcap_pid)
        self._disconnect()

class SSHCleanupWorker(SSHWorker):
    '''Performs cleanup operations on a remote host. Those operations include
    the removal of all created directories as well as the deletion of files
    that were copied to the host.
    '''
    def __init__(self, hostname, configuration, username="", password=""):
        SSHWorker.__init__(self, hostname, username, password)
        self._configuration = configuration
        
    def run(self):
        '''Connects to the specified host, removes all previously created
        directories and files, as well as those files that were created
        during the execution of the distributed testbed (notably logs,
        full downloads, ...). Terminates the connection immediately after
        the given host was cleaned up.
        
        Return:
            NoneType
        '''
        self._connect()
        self._remove_directory_structure()
        self._remove_files()
        self._disconnect()
        
    def _remove_directory_structure(self):
        '''Removes the testbed directory structure on the specified host.
        
        Return:
            NoneType
        '''
        for dpl in self._configuration.get_deployments().values():
            if self._hostname not in dpl.get_hostlist():
                continue
            base_dir = dpl.get_remote_base_directory()
            if base_dir != "/":
                self._run_cmd("rm -rf %s" % base_dir)
    
    def _remove_files(self):
        '''Collects all remote files that were copied to the host and deletes
        them afterwards.
        
        Return:
            NoneType
        '''
        host_files = ["pcap.log"]
        for dpl in self._configuration.get_deployments().values():
            schema = dpl.get_client_conf_schema()
            hostlist = dpl.get_hostlist()
            if self._hostname not in hostlist:
                continue
            
            check_list = []
            check_list += schema.get_leeching_list()
            check_list += schema.get_seeding_list()
            check_list = remove_duplicate_elements_from_list(check_list)
            check_list = [self._configuration.get_files()[file].get_relative_filename()
                          for file in check_list]
            
            for file in check_list:
                if file not in host_files:
                    torrent = str(file) + constants.TORRENT_DOWNLOAD_EXT
                    host_files.append(file)
                    host_files.append(torrent)
        
        for file in host_files:
            self._logger.info("Deleting file %s on %s" % (file, self._hostname))
            self._run_cmd("sudo rm %s" % file)
            
#_______________________________________________________________________________
# FUNCTIONS
            
def _parse_grep_response(response):
    '''This function parses a line of the output of a remotely executed grep 
    command. It extracts and returns the pid number of the respective process.
    
    Parameter:
        response -- A single line from a list of processes (describing a single
                    process)
        
    Return:
        Integer value that represents the parsed PID number of the process
        the given line refers to. 
    '''
    for token in response.split(" ")[1:]:
        if token == "":
            continue
        return int(token)