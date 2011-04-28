import string
import logging
import sys

from SisClient.Testbed.TestbedConfig import *
from SisClient.Testbed.TestbedConfigChecker import TestbedConfigurationChecker
from SisClient.Testbed.Utils.configparser import LinewiseConfigParser
from Conditions import *

# some global variables that get filled during the parsing
clients = {}
filesToSeed = {}
baseDirectory = ""
sis_url = None
assignedPorts = []
tracker = {}
list_of_conditions = []

def read_base_directory(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token BaseDirectory at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global baseDirectory
    assert len(tokens) >= 2
    
    for token in tokens[1:]:
        baseDirectory += token + " "
    baseDirectory = string.rstrip(baseDirectory)
    baseDirectory = baseDirectory.replace("\n", "")
    
    if not baseDirectory.endswith(os.path.normcase('/')):
        baseDirectory += os.path.normcase('/')
    
def read_sis_url(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token SIS_URL at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global sis_url
    assert len(tokens) == 2
    sis_url = tokens[1]
    sis_url = sis_url.replace("\n", "")

def read_file_to_seed(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token FileToSeed at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global filesToSeed
    assert len(tokens) >= 3
    
    fileId = int(tokens[1])
    fileLocation = ""
    for token in tokens[2:]:
        fileLocation += token + " "
    fileLocation = string.rstrip(fileLocation)
    fileLocation = fileLocation.replace("\n", "")
    
    # store a tuple of the form (absolute path to file, torrent created,
    # absolute path to torrent file) in a hash with key == given id
    # the values that are False and None here will be set later
    # by the internal tracker
    filesToSeed[fileId] = (fileLocation, False, None)   
        
def read_seeder(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token Seeder at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global clients
    assert len(tokens) > 2
    
    seedingList = []
    for token in tokens[2:]:
        seedingList.append(int(token))
    id = int(tokens[1])
    
    clientspec = {}
    if id in clients.keys():
        clientspec = clients[id]
        
    clientspec['seeding'] = seedingList
    clients[id] = clientspec
    
def read_leecher(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token Leecher at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global clients
    assert len(tokens) > 2
    
    leechingList = []
    for token in tokens[2:]:
        leechingList.append(int(token))
    id = int(tokens[1])
    
    clientspec = {}
    if id in clients.keys():
        clientspec = clients[id]
    clientspec['leeching'] = leechingList
    clients[id] = clientspec
        
def read_client_mode(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token ClientMode at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global clients
    assert len(tokens) >= 6

    clientspec = {}
    id = int(tokens[1])
    if id in clients.keys():
        clientspec = clients[id]

    clientspec['id'] = int(tokens[1])
    clientspec['neighbour'] = tokens[2].__str__().replace("\n", "")
    clientspec['peer'] = tokens[3].__str__().replace("\n", "")
    clientspec['uprate'] = int(tokens[4])
    clientspec['downrate'] = int(tokens[5])
    
    port = -1
    if len(tokens) == 7:
        # port number was specified, so read it
        port = int(tokens[6])
    else:
        port = get_random_bootstrap_port()
    clientspec['port'] = port
    
    clients[id] = clientspec
            
def read_tracker(tokens):
    '''
    Helper function for reading a testbed configuration. Is triggered if the
    instance of a LinewiseConfigParser sees the token Tracker at the
    beginning of a line. Reads the parameters that go along with that line.
    '''
    global tracker
    assert len(tokens) >= 3
    
    tracker['uprate'] = int(tokens[1])
    tracker['downrate'] = int(tokens[2])
    
    if len(tokens) is 4:
        # port number was specified, so read it
        tracker['port'] = int(tokens[3])
    else:
        tracker['port'] = get_random_bootstrap_port()
        
def read_is_leeching(tokens):
    '''Helper function for reading a testbed configuration. Is triggered
       if the instance of a LinewiseConfigParser sees the token "IsLeeching"
       at the beginning of a line. Reads the parameters that go along with
       that line as well.
    '''
    global list_of_conditions
    assert len(tokens) == 2
    
    client_id = int(tokens[1])
    condition = IsLeechingCondition(client_id)
    list_of_conditions.append(condition)

def read_is_seeding(tokens):
    '''Helper function for reading a testbed configuration. Is triggered
       if the instance of a LinewiseConfigParser sees the token "IsSeeding"
       at the beginning of a line. Reads the parameters that go along with
       that line as well.
    '''
    global list_of_conditions
    assert len(tokens) == 2
    
    client_id = int(tokens[1])
    condition = IsSeedingCondition(client_id)
    list_of_conditions.append(condition)

def read_finished_downloading(tokens):
    '''Helper function for reading a testbed configuration. Is triggered
       if the instance of a LinewiseConfigParser sees the token 
       "FinishedDownload" at the beginning of a line. Reads the parameters
       that go along with that line as well.
    '''
    global list_of_conditions
    assert len(tokens) == 3
    
    client_id = int(tokens[1])
    filename = tokens[2]
    list_of_conditions.append(FinishedDownloadCondition(client_id, filename))

def read_changed_status_to(tokens):
    '''Helper function for reading a testbed configuration. Is triggered
       if the instance of a LinewiseConfigParser sees the token 
       "ChangedStatusTo" at the beginning of a line. Reads the parameters
       that go along with that line as well.
    '''
    global list_of_conditions
    assert len(tokens) == 5
    
    client_id = int(tokens[1])
    status_from = tokens[2]
    status_to = tokens[3]
    filename = tokens[4]
    list_of_conditions.append(ChangedStatusCondition(client_id, status_from,
                                                     status_to, filename))

def finalize():
    global clients, filesToSeed, baseDirectory, sis_url, tracker
    global list_of_conditions
    
    conf = TestbedConfiguration()
    conf.set_test_name("Test constructed from external declaration")
    conf.set_base_directory(baseDirectory)
    
    for fileId in filesToSeed.keys():
        conf.add_file(fileId, filesToSeed[fileId][0])
    
    for client in clients.values():
        c = conf.add_client(client['id'])
        c.set_base_directory(baseDirectory)
        c.set_port(client['port'])
        c.set_uprate(client['uprate'])
        c.set_downrate(client['downrate'])
        c.set_sis_url(sis_url)
        c.set_neighbour_selection_mode(client['neighbour'])
        c.set_peer_selection_mode(client['peer'])
        
        if 'seeding' not in client.keys():
            client['seeding'] = []
        if 'leeching' not in client.keys():
            client['leeching'] = []
        
        for fileId in client['seeding']:
            c.add_file_to_seed(fileId)
        for fileId in client['leeching']:
            c.add_file_to_leech(fileId)
            
    t = conf.add_tracker()
    t.set_base_directory(baseDirectory)
    t.set_uprate(tracker['uprate'])
    t.set_downrate(tracker['downrate'])
    tracker_url = "http://localhost:%i/announce" % tracker['port']
    t.set_url(tracker_url)
    
    for condition in list_of_conditions:
        conf.add_condition(condition)
        
    ok, errors, warnings = TestbedConfigurationChecker.is_consistent(conf)
    for warning in warnings:
        logging.info("WARNING: %s" % warning)
    if not(ok):
        logger = logging.getLogger()
        logger.info("TestbedConfiguration is not consistent.")
        for error in errors:
            logging.info("ERROR: %s" % error)
        sys.exit()
    
    dir(conf)
    
    return conf
    
def read_specification(file):
    mapping = {
                "Seeder"        :       read_seeder,
                "Leecher"       :       read_leecher,
                "BaseDirectory" :       read_base_directory,
                "FileToSeed"    :       read_file_to_seed,
                "SIS_URL"       :       read_sis_url,
                "Client"        :       read_client_mode,
                "Tracker"       :       read_tracker,
                "IsLeeching"    :       read_is_leeching,
                "IsSeeding"     :       read_is_seeding,
                "FinishedDownload"  :   read_finished_downloading,
                "ChangedStatusTo"   :   read_changed_status_to
    }
    
    parser = LinewiseConfigParser(file, mapping, None)
    parser.parse()
    
    return finalize()