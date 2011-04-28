import os
import sys
import optparse
import tempfile
import time
import logging
import logging.config
import random

from SisClient.Testbed.Utils.utils import *
from BaseLib.Core.API import *

from SisClient.Tools.add_playtime import videostats_via_ffmpeg
from SisClient.Common import constants

logger = None

'''
You dont have to create an instance of the tracker class if you use the tracker
in a separate process anyways. It is sufficient to call this script with the
appropriate parameters. If you run the script with

python tracker.py
    
you will get list of possible parameters to configure the tracker. A minimal
tracker that tracks a specific torrent can be instantiated by executing
the following command:

python SisClient/Testbed/tracker.py -h
'''

temp_dirs = []

class Tracker:
    '''
    You can use this class if you want to have a client in your network
    that is also capable of tracking torrents and creating torrent files
    that direct to this tracker. Please note the tracker works in the standalone fashion,
    i.e. it will NOT participate in the swarm.
    
    The class itself is configurable in different ways.
    
    If you pass an admissible value for the filesDirectory into the
    constructor, the class will look at this directory and create torrents
    for every file it finds. The torrents that were created during this 
    process will be started afterwards. However, if you pass in NoneType, 
    this behaviour is suppressed.
    
    If you want the tracker to track only one specific torrent file, you pass
    in an admissible value for the singleTorrent parameter. If you do so, and
    you have specified a filesDirectory, the creation of torrents for files
    in that directory will be suppressed.
    
    Please note that you do not have to use any of these options. If you 
    just want to start a tracker, you can leave those parameters out.
    '''
    def __init__(self, directory, url, pieceSize, filesDirectory=None, \
                 singleTorrent=None, vod = False):
        global temp_dirs
        # Fetches a logger instance addressed by the class's name
        self._logger =  logging.getLogger(self.__class__.__name__)
        # The directory at which the tracker stores created torrents and
        # possible downloads.
        self._directory = directory
        
        #whether we should try to generate streamable torrents
        self._vod = vod
        
        # set url and port to default values, check afterwards if the user
        # provided some values for them and see if they are compliant
        # to our tracker url/port specification
        self._port = random.randint(8500, 9000)
        self._url = "http://localhost:%d/announce" % self._port
        # if url is not None, we might have to alter port and url
        if url is not None:
            # verify and extract port number from it
            if verify_tracker_url(url):
                port = extract_tracker_port_from_url(url)
                self._url = url
                self._port = port
        print >> sys.stderr, "Tracker runs at %s" % self._url            
        
        # piece size of the torrents the tracker creates
        self._pieceSize = pieceSize
        # directory at which the tracker looks upon starting up 
        # for flies for which it shall create torrents - can be None
        self._filesDirectory = filesDirectory
        # specific torrent file - can be None
        self._singleTorrent = singleTorrent
        # init value for _session
        self._session = None
        self._state_directory = tempfile.mkdtemp()
        temp_dirs.append(self._state_directory)
        set_exit_handler(self._clean_up)
        
    def start_tracker(self):
        '''
        Creates a session instance and looks for torrent files in the trackers
        directory. Starts the download of those torrents. This has to be done,
        because the tracker wont work correctly if you dont start them.
        Unfortunately, by doing so, the tracker acts as a client as well and
        tries to download/seed the corresponding files.
        '''
        scfg = SessionStartupConfig()
        #scfg.set_state_dir(tempfile.mkdtemp(dir=TEMP_DIR))
        scfg.set_state_dir(self._state_directory)
        if not self._port is -1:
            scfg.set_listen_port(self._port)
        scfg.set_overlay(False)
        scfg.set_megacache(False)
        scfg.set_upnp_mode(UPNPMODE_DISABLED)
        if not self._url is None:
            scfg.set_internal_tracker_url(self._url)
        
        self._logger.info("instantiating session")
        self._session = Session(scfg)
        self._logger.info("creating torrents")
        
        if self._singleTorrent is None:
            # create torrents for those files that are found
            # at the files directory
            torrents = self._create_torrents()
        else:
            # start the single torrent
            if os.path.isfile(self._singleTorrent):
                torrents = [self.start_singleTorrent(self._singleTorrent)]
            elif os.path.isdir(self._singleTorrent):
                allowed = [constants.TORRENT_DOWNLOAD_EXT, constants.TORRENT_VOD_EXT]
                torrents_to_start = files_list(self._singleTorrent, allowed)
                torrents = []            
                for torrent in torrents_to_start:
                    torrents.append(self.start_single_torrent(torrent))
            else:           
                self._logger.info("neither torrent file nor directory with torrents found:"+self._singleTorrent)
                sys.exit(1)
        
        if len(torrents) == 0:
            self._logger.error("No torrents found. Exit")
            sys.exit(-1)
        for tdef in torrents:
            self._session.add_to_internal_tracker(tdef)
            
        self._logger.info("Started %d torrents " % len(torrents))
        self._logger.info("tracker is listening at url %s" % 
                           self._session.get_internal_tracker_url())
        
    def _clean_up(self, signal=None, func=None):
        global temp_dirs
        
        self._logger.info("Cleaning up...")
        self.shutdown_tracker()
        for dir in temp_dirs:
            self._logger.info("Removing directory at %s" % dir)
            FileUtils.remove_directory_recursively(dir)
        self._logger.info("Tracker shut down, directories were removed.")
        sys.exit()
        
    def shutdown_tracker(self):
        '''Propagates a shutdown signal to the Session object, which should
           render the tracker inactive.
        '''
        if self._session is not None:
            self._logger.debug("Shuttding down the session...")
            self._session.shutdown()
            self._logger.debug("Give it some time to shutdown properly...")
            time.sleep(3) # 3 seconds
            self._session = None
        
    def start_single_torrent(self, file):
        '''
        If you already have a torrent file, you can start it by passing
        it to this method.
        '''
        tdef = TorrentDef.load(file)
        return tdef
        
    def create_torrent(self, file):
        '''
        Creates a torrent for the given file. Returns a string representing the
        path to the torrent file.
        '''

        tdef = TorrentDef()
        tdef.set_tracker(self._session.get_internal_tracker_url())
        tdef.set_create_merkle_torrent(False)
        tdef.set_piece_length(self._pieceSize)
        
        if self._vod:
            torrent_ext = constants.TORRENT_VOD_EXT
            # set playtime
            try:
                playtime = videostats_via_ffmpeg(file)['playtime']
            except:
                self._logger.warn("Cannot create streaming torrent for file %s" % file)
                return
            self._logger.debug("playtime %s" % playtime)
        else:
            torrent_ext = constants.TORRENT_DOWNLOAD_EXT
            playtime = None
            self._logger.warning("Create a non-streamable torrent")
                
        tdef.add_content(file, playtime=playtime)
        
        tdef.finalize()
        torrent = os.path.join(self._directory, FileUtils.get_relative_filename(file) + torrent_ext)
        tdef.save(torrent)
            
        self._logger.info("created torrent file: %s" % torrent)
        self._logger.info("Tracker uses the announce URL: %s" % tdef.get_tracker())

        return tdef
    
    def _create_torrents(self):
        '''
        Creates for every regular file in the specified directory a torrent file
        which is stored at the trackers directory. A corresponding download will
        be started.
        '''
        if self._filesDirectory is None:
            return 0
        
        # walk through the files directory and create torrents
        torrents = []
        for file in os.listdir(self._filesDirectory):
            if file.endswith('.svn') or file.endswith(constants.TORRENT_VOD_EXT) or file.endswith(constants.TORRENT_VOD_EXT):
                self._logger.warning("Don't create torrent for file: %s" % file)
            else:
                #do not index svn files and torrents 
                tdef = self.create_torrent(self._filesDirectory + file)
                if tdef: 
                    torrents.append(tdef) 
        return torrents
            
    def track_forever(self):
        '''
        Starts the trackers and runs it until it receives a keyboard interrupt.
        '''
        self.start_tracker()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self._logger.info("Catching KeyboardInterrupt")
            self._clean_up()
            sys.exit()
            
#___________________________________________________________________________________________________
# FUNCTIONS 

def parse_tracker_options():
    '''
    Uses Pythons option parser to parse the arguments that were given
    via the command line. Runs a fix integrality check and ensures that
    directories always have a trailing /.
    '''
    parser = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options]",
                                   description="Required parameters are: files directory OR (already existing) torrent file(s)",
                                   version=sys.argv[0] + " 0.1")
    parser.add_option("-f", "--files_directory",
                      action="store", dest="filesDirectory", default=None,
                      help="Specifies the directory which contains the files " +
                      "for that the tracker shall create torrent files.")
    parser.add_option("-d", "--directory",
                      action="store", dest="directory", default=None,
                      help="Specifies the directory of the tracker. Since the " +
                      "tracker also acts as a client, this directory contains " +
                      " torrent files and (possibly) downloads.")
    parser.add_option("-u", "--url",
                      action="store", dest="url", default=None,
                      help="Specifies the tracker's url, it must have the format http://your-url:PORT/announce" +\
                       " NOTE that by default the tracker will use a RANDOM port number.")
    parser.add_option("-s", "--piece_size",
                      action="store", type="long", dest="pieceSize", 
                      default=constants.DEFAULT_PIECE_LENGTH,
                      help="Specifies the piece size for created torrents.")
    parser.add_option("-t", "--torrents",
                      action="store", dest="singleTorrent",
                      default=None,
                      help="Path to already existing torrent file or directory with torrent files"+\
                      "Please note that in this case the tracker will not use the files_directory option."+ \
                      "+++++WARNING++++: make sure that you set the torrent announce URL according to tracker's HOSTNAME and especially PORT!")
    parser.add_option("-i", "--ignore_log",
                      action="store_true", dest="ignoreLog", default=False,
                      help="(DEPRECATED) Turn this switch on if you want to ignore all log output.")
    parser.add_option("-v", "--vod",
                      action="store_true", dest="vod", default=False,
                      help="Try to generate streaming torrents.")
    
    (options, args) = parser.parse_args()
    
    # check if download directory needs to be temporarily created
    print options.directory
    if options.directory is None:
        options.directory = tempfile.mkdtemp()
        temp_dirs.append(options.directory)
    else:
        if not options.directory.endswith(os.path.normcase('/')):
            options.directory += os.path.normcase('/')
            if not os.access(options.directory, os.F_OK):
                FileUtils.create_directory(options.directory)
        
    if options.filesDirectory is None and options.singleTorrent is None:
        parser.error("You have to specify either the file directory or the single file to track.")
        parser.print_help()
        sys.exit()        
        
    print "use tracker directory: %s" % options.directory
    
    # verify the url parameter using a regex
    if options.url is not None:
        if not verify_tracker_url(options.url):
            parser.error('The tracker url must follow the pattern: ' +
                         'http://your-url:PORT/announce instead of %s' % options.url)
            parser.print_help()
            sys.exit(-1)
        
    if options.filesDirectory is not None:
        #TODO: check if it is empty!
        if not os.access(options.filesDirectory, os.F_OK):
            parser.error("The files directory is not accessible.")
            sys.exit()
        if not options.filesDirectory.endswith(os.path.normcase('/')):
            options.filesDirectory += os.path.normcase('/')
    
    if options.singleTorrent is not None:
        if not os.access(options.singleTorrent, os.F_OK):
            parser.error("The torrent file you specified does not exist.")
            sys.exit()
        
    if not options.directory.endswith(os.path.normcase('/')):
        options.directory += os.path.normcase('/')
        
    return (options, args)

#___________________________________________________________________________________________________
# MAIN

if __name__ == '__main__':
    levels = {"DEBUG":logging.DEBUG, "INFO":logging.INFO, "WARN":logging.WARN, "ERROR":logging.ERROR, "CRITICAL":logging.CRITICAL, "FATAL":logging.FATAL}
    (options, args) = parse_tracker_options()
    
    logging.config.fileConfig("config/log_client.conf")
    if options.ignoreLog is True:
        for level in levels.values():
            logging.disable(level)

    tracker = Tracker(options.directory, options.url, options.pieceSize, \
                      options.filesDirectory, options.singleTorrent, options.vod)
    tracker.track_forever()
