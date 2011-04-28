# just some convenience methods that we use throughout the project

import os
import logging
import logging.handlers
from binascii import b2a_hex
from binascii import a2b_hex
from BaseLib.Core.TorrentDef import TorrentDef
from SisClient.Common import constants

def get_id(tdef):
        ''' Derive a hex-encoded infohash-based id of the torrent.
        '''
        return b2a_hex(tdef.get_infohash())
    
def convert_binary_string_to_hex(binstr):
    return b2a_hex(binstr)

def convert_hex_string_to_binary(hexstr):
    return a2b_hex(hexstr)

def iop_url_from_sis_url(sis_url="http://localhost:8080/sis"):
    '''Constructs the URL of the IoP endpoint based on the SIS URL.
    
    Arguments:
        sis_url    -- URL of the SIS server
        
    Returns:
        URL of the IoP endpoint
    '''
    if not sis_url.endswith('/'):
        sis_url += '/'
    return sis_url + 'IoPEndpoint'

def hap_url_from_sis_url(sis_url="http://localhost:8080/sis"):
    '''Constructs the URL of the HAP endpoint based on the SIS URL.
    
    Arguments:
        sis_url    --    URL of the SIS server
        
    Returns:
        URL of the HAP endpoint
    '''
    if not sis_url.endswith('/'):
        sis_url += '/'
    return sis_url + 'HAPEndpoint'

def client_url_from_sis_url(sis_url="http://localhost:8080/sis"):
    '''Constructs the URL of the client endpoint based on the SIS URL.
    
    Arguments:
        sis_url    -- URL of the SIS server
        
    Returns:
        URL of the client endpoint
    '''
	# For the case that no SIS ranking is used the url is just "None"
    if sis_url == None:
        return None
    
    if not sis_url.endswith('/'):
        sis_url += '/'
    return sis_url + 'ClientEndpoint'

def get_torrents(folder): 
    ''' Returns the dictionary {infohash : (torrent_definition, file_name)}
    for all torrent files in the given directory.
    '''
    fileObjects = os.listdir(folder)
    torrent_files = []
    for file in fileObjects:
        if str(file).endswith(constants.TORRENT_DOWNLOAD_EXT) or str(file).endswith(constants.TORRENT_VOD_EXT):
            torrent_files.append(os.path.join(folder, str(file)))
    files = sorted(torrent_files)
    
    torrents = dict()
    
    for file in files:
        
        tdef = TorrentDef.load(file)
        id = get_id(tdef)
        torrents[id] = (tdef, file)
    return torrents

# string representations are associated with every termination condition
exit_on_to_string_map = { constants.EXIT_ON_ALL_FINISHED    :   "download",
                          constants.EXIT_ON_SEEDING_TIME    :   "seeding",
                          constants.EXIT_ON_PLAYBACK_DONE   :   "playback"}

string_to_exit_on_map = { 'download'    : constants.EXIT_ON_ALL_FINISHED,
                          'seeding'     : constants.EXIT_ON_SEEDING_TIME,
                          'playback'    : constants.EXIT_ON_PLAYBACK_DONE}

def get_exit_on_as_string(exit_on_as_int):
    '''Retrieves the String representation of the termination condition
    "enumeration".
    
    Parameter:
        exit_on_as_init -- Integer value that represents a termination condition
        
    Return:
        String representation of the given termination condition.
    '''
    return exit_on_to_string_map[exit_on_as_int]

def get_exit_on_from_string(exit_on_as_string):
    try:
        return string_to_exit_on_map[exit_on_as_string]
    except:
        return constants.EXIT_ON_ALL_FINISHED
    
def has_torrent_video_files(tdef):
#    video_files_suffixes = ['mpg', 'mp4', 'mov', 'avi', 'mkv', 'wmv']
#    list_of_files = tdef.get_files()
#    for file in list_of_files:
#        suffix = file[file.rindex('.')+1:]
#        if suffix in video_files_suffixes:
#            return True
#    return False
    return tdef.get_bitrate()!=None

def setup_cache_file_logger(logfile):
    file_handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024*1024)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(file_handler)
    logging.getLogger('Tribler').addHandler(file_handler)
    logging.getLogger('Status').addHandler(file_handler)
    logging.getLogger('Cache').addHandler(file_handler)
    
def setup_client_file_logger(logfile):
    file_handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024*1024)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(file_handler)
    logging.getLogger('Status').addHandler(file_handler)
    logging.getLogger('Communicator').addHandler(file_handler)
    logging.getLogger('Client').addHandler(file_handler)