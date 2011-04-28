from SisClient.Common import constants
import logging
import optparse
import os
import sys
import threading
import time
import random

from SisClient.Testbed.Distributed import dist_config_parser
from SisClient.Testbed.Distributed.ssh_workers import SSHRunTrackerWorker
from SisClient.Testbed.Distributed.ssh_workers import SSHRunClientWorker
from SisClient.Testbed.Distributed.ssh_workers import SSHKillTrackerWorker
from SisClient.Testbed.Distributed.ssh_workers import SSHKillAllWorker
from SisClient.Testbed.Distributed.ssh_workers import SSHCleanupWorker
from SisClient.Testbed.Distributed.ssh_workers import SSHExecuteCommandWorker
from SisClient.Testbed import logger
from SisClient.Testbed.Utils.utils import *

#_______________________________________________________________________________
# MODULE VARIABLES
# if you use those variables in a function, please refer to them using the
# keyword global for clarity
options = None
args = None
cfg = None
is_running = False

#_______________________________________________________________________________
# PRIVATE SECTION
    
def _launch_tracker():
    '''Runs an SSH worker that starts the tracker on the specified host. The
    testbed execution will wait for a specified amount of time (see option
    tracker time). After that time, the torrent files that the tracker
    has created are being copied to the local machine, from where they
    can be distributed to other hosts.
    '''
    global cfg
    global options
    
    # resolve hostname
    hostname = cfg.get_hosts()[cfg.get_tracker().get_hostname()]
    
    # copy files to tracker host
    files = cfg.get_tracker().get_files()
    for file in files:
        filename = cfg.resolve_file_ref(file)
        os.system("scp %s %s@%s:/home/%s" % (filename, options.username, 
                                             hostname, options.username))
    
    # start tracker
    worker = SSHRunTrackerWorker(hostname, cfg, username=options.username)
    worker.run()
    
    logging.info("Waiting %i seconds for tracker to create torrent files..." %
                 cfg.get_tracker().get_waiting_time())
    time.sleep(cfg.get_tracker().get_waiting_time())
    
    # fetch torrents
    logging.info("Fetching torrent files from remote tracker directory...")
    remote_base_dir = cfg.get_tracker().get_base_directory()
    remote_tracker_dir = "%stracker" % remote_base_dir
    for file in files:
        filename = cfg.get_files()[file].get_relative_filename() + constants.TORRENT_DOWNLOAD_EXT
        os.system("scp %s@%s:%s/%s %s" % (options.username, hostname,
                                          remote_tracker_dir, filename, filename))
        
def _launch_pcap():
    global cfg
    global options
    
    remote_file = "/home/%s/pcap.log" % options.username
    cmd = "cd tribler; sudo sh pcap.sh eth0 --mode=live --log=%s" % remote_file
    
    for host in cfg.get_hosts().values():
        logging.info("Starting packet capture on host %s" % host)
        worker = SSHExecuteCommandWorker(host, cmd, username=options.username)
        worker.run()
        
def _kill_all():
    global cfg
    global options
    
    for host in cfg.get_hosts().values():
        logging.info("Killing every remaining remote process on host %s" % host)
#        logging.info("Killing packet capture process on host %s" % host)
        worker = SSHKillAllWorker(host, username=options.username)
        worker.start()
        
def _copy_files_to_remote_hosts():
    '''This method copies relevant files to all specified hosts in the testbed
    cluster. Those files include full downloads as well as torrent files, so
    it is crucial that the tracker gets started before this method will be
    invoked.
    '''
    def _build_host_to_file_dict():
        '''Builds a dictionary which stores key-value pairs of the form:
        (hostname, list of files). The list of files does not contain
        duplicate entries.
        '''
        htoloff = {}
        for deployment in cfg.get_deployments().values():
            for hostname in deployment.get_hostlist():
                if hostname not in htoloff.keys():
                    htoloff[hostname] = []
                schema = deployment.get_client_conf_schema()
                _add_files_to_mapping(schema.get_leeching_list(), htoloff[hostname])
                _add_files_to_mapping(schema.get_seeding_list(), htoloff[hostname])
        return htoloff
    
    def _add_files_to_mapping(list_of_files, mapping_list):
        '''Adds files from the first list to a host-to-files list (second list),
        if there are not already present there.
        '''
        for file in list_of_files:
            if file not in mapping_list:
                mapping_list.append(file)
    
    def _resolve_file_references(htoloff):
        '''Referenced files go by a short keyname in the configuration. such
        references will be resolved by this method.
        '''
        files = cfg.get_files()
        for key in htoloff.keys():
            for file_ref in htoloff[key]:
                htoloff[key].remove(file_ref)
                htoloff[key].append(files[file_ref].get_absolute_path_to_file())
    
    def _copy_files(htoloff):
        '''Performs the actual copy process of files. Utilizes 'scp' to do so.
        '''
        for host_key in htoloff.keys():
            logging.info("Copying files to remote host %s" % host_key)
            for file in htoloff[host_key]:
                torrent = FileUtils.get_relative_filename(file) + constants.TORRENT_DOWNLOAD_EXT
                os.system("scp %s %s@%s:/home/%s" % (file, options.username, host_key, options.username))
                os.system("scp %s %s@%s:/home/%s" % (torrent, options.username, host_key, options.username))
                
    global options
    global cfg
    
    htoloff = _build_host_to_file_dict()
    _resolve_file_references(htoloff)
    _copy_files(htoloff)
    
def _shutdown_testbed(clonh):
    '''Performs a graceful shutdown of the distributed testbed. This includes
    the termination of remote clients, the fetching of logfiles and the
    (optional) removal of all remote files that were created or copied during
    the testbed's execution.
    '''
    global options
    global cfg
    
    hostname = cfg.get_hosts()[cfg.get_tracker().get_hostname()]
    worker = SSHKillTrackerWorker(hostname, options.username)
    worker.start()
    _kill_all()
    _fetch_logfiles(clonh)
    if cfg.remove_remote_files():
        _remove_remote_files()
    is_running = False
    
def _clients_to_hosts_dict(clonh):
    '''Helper method. Somewhat transposes the clients dict that is used
    in run_simulation.
    key-value format:
    old: (client -> (host, deployment))
    new: (host   -> (client, deployment))
    '''
    host_dict = {}
    for client_id in clonh.keys():
        hostname, dpl = clonh[client_id]
        if hostname not in host_dict.keys():
            host_dict[hostname] = [(client_id, dpl)]
        else:
            host_dict[hostname].append((client_id, dpl))
    return host_dict
    
def _fetch_logfiles(clonh):
    '''Copies logfiles from all remote processes to the local folder specified
    in options.logfile. If there is an already existing local folder at
    options.logfile, the contents of it will be overriden withouth further
    notice.
    '''
    global options
    global cfg
    
    logfile_directory = cfg.get_logfile_directory()
        
    FileUtils.create_directory(logfile_directory, removeOld=True)
    host_dict = _clients_to_hosts_dict(clonh)
    for host in host_dict.keys():
        local_logfile_dir_for_host = logfile_directory + host
        local_pcap_file = local_logfile_dir_for_host + os.path.normcase('/') + "pcap.log"
        FileUtils.create_directory(local_logfile_dir_for_host, removeOld=True)
        
        # copy packet capture log to local machine
        os.system("scp %s@%s:/home/%s/%s %s" % (options.username,
                                                host,
                                                options.username,
                                                "pcap.log",
                                                local_pcap_file))
        
        for client_id, dpl in host_dict[host]:
            base_dir = cfg.get_deployment_by_name(dpl).get_remote_base_directory()
            client_local_logfile = local_logfile_dir_for_host + \
                os.path.normcase('/') + "client%i.log" % client_id
            client_remote_logfile = "%sclient%i/client%i.log" % (base_dir,
                                                                 client_id,
                                                                 client_id)
            os.system("scp %s@%s:%s %s" % (options.username,
                                           host,
                                           client_remote_logfile,
                                           client_local_logfile))
            
def _remove_remote_files():
    '''Starts worker threads that perform cleanup operations on remote hosts.
    '''
    global cfg
    global options
    
    for host in cfg.get_hosts().values():
        logging.info("Starting cleanup worker on %s" % host)
        worker = SSHCleanupWorker(host, cfg, username=options.username)
        worker.start()

def _read_configuration(configuration_file):
    '''Reads the specified configuration file. Checks if it is present in the
    filesystem. If not, the execution of the script will be terminated.
    '''
    global cfg
    
    if not os.access(configuration_file, os.F_OK):
        logging.info("Missing referenced configuration file.")
        sys.exit(1)
    cfg = dist_config_parser.parse_distributed_configuration(configuration_file)
    logging.info("Read configuration file.")
    
def _parse_options():
    '''Parses command-line arguments and options.
    '''
    global options
    global args
    
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + \
                                   " <config> [options]")
    parser.add_option("-u", "--user",
                      action="store", dest="username", default="tud_p2p",
                      help="Specifies the remote user's name")
    
    options, args = parser.parse_args()
    
    if len(args) == 0:
        logging.info("Missing required positional arguments.")
        sys.exit(1)

#_______________________________________________________________________________
# PUBLIC SECTION

def run_simulation():
    '''Performs the actual execution of the testbed. Steps involved are:
    * Launch tracker
    * Fetch torrent files from tracker
    * Distribute full downloads and torrent files to remote hosts
    * Start the experiment
      * Look for birth events and execute them as appropriate
    * Gracefully shutdown the testbed after the completion of the experiment
    '''
    global username
    global cfg
    global options
    global is_running
    
    _launch_tracker()
    _copy_files_to_remote_hosts()
    _launch_pcap()

    events = cfg.get_events()
    is_running = True
    start_time = time.time()
    client_to_hostnames = {}
    while is_running:
        try:
            current_time = time.time() - start_time
            # loop through list of events
            # fetch those events that have to be executed
            # prioritize them by birth/death tasks
            events_for_exec = [event for event in events if event[1] <= current_time]
            events_for_exec.sort(lambda x,y: cmp(x[0], y[0]))
            # remove those events from the event list
            events = [event for event in events if event not in events_for_exec]
            # now start birth workers for those events in sep. threads
            for event in events_for_exec:
                # every event is a birth event
                dpl = cfg.get_deployment_by_name(event[2])
                hostlist = dpl.get_hostlist()
                hostidx = random.randint(0, len(hostlist)-1)
                client_to_hostnames[event[1]] = (hostlist[hostidx], event[2])
                worker = SSHRunClientWorker(event, cfg, hostlist[hostidx],
                                            username=options.username)
                worker.start()
             
            if current_time >= cfg.get_timeout():   
                # our testbed has come to an end, trigger shutdown
                _shutdown_testbed(client_to_hostnames)
                is_running = False
            
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Caught a KeyboardInterrupt. Exiting...")
            _shutdown_testbed(client_to_hostnames)
            sys.exit(1)
    time.sleep(5)
    sys.exit(0)

def main():
    '''Parses options, reads configuration, starts the simulation.'''
    global args
    
    logger.init_logger(None, logging.INFO)
    _parse_options()
    _read_configuration(args[0])
    run_simulation()
        
#_______________________________________________________________________________
# MAIN
    
if __name__ == "__main__":
    main()