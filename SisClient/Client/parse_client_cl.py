import optparse
import sys

def parse_client_options(cl):
    '''
    Uses Pythons option parser to parse the arguments that were given
    via the command line. Runs a fix integrality check and ensures that
    directories always have a trailing /.
    '''
    assert type(cl) == list
    
    parser = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options]", 
                                   description="Required params are: torrent file (if no torrent files are located in the client directory).", version=sys.argv[0] + " 0.1")

    parser.add_option("-p", "--port",
                      action="store", type="int", dest="port", default=None,
                      help="Specifies the port on which the client runs.")
    
    parser.add_option("-i", "--id",
                      action="store", type="int", dest="id", default=None,
                      help="Specifies the client's id.")
    
    parser.add_option("-d", "--directory",
                      action="store", dest="directory", default=None,
                      help="Specifies the directory where torrents and downloads " + \
                      "are stored.")
    
    parser.add_option("-t", "--temporary_state_directory",
                      action="store", dest="temporary_state_directory",
                      default=None,
                      help="Specifies the directory where state files will be " + \
                      "stored.")
    
    parser.add_option("-l", "--logfile", 
                      action="store", dest="logfile", default=None,
                      help="Specifies to where the client shall write the logfile. " + \
                      "If you suppress this parameter, the log will not be written " + \
                      "to an output file.")
    
    parser.add_option("-m", "--peer_selection_mode",
                      action="store", dest="mode_ps", default=None,
                      help="Enables the peer selection mode (none|enable)")
    
    parser.add_option("-n", "--neighbour_selection_mode",
                      action="store", dest="mode_ns", default=None,
                      help="Enable the peer selection mode (none|enable)")
    
    parser.add_option("-b", "--ranking_source",
                      action="store", dest="ranking_source", default=None,
                      help="set the source and type of peer rankings operation mode of neighbor selection (none|samehost|geoip|odd_even|sis|sis_simple|ip_pre)")
    
    parser.add_option("-u", "--sis_url",
                      action="store", dest="sis_url", default=None,
                      help="Specifies the SIS url of the form: 'http://<hostname>:<port>/sis'")
    
    parser.add_option("-x", "--upload",
                      action="store", type="int", dest="upload", 
                      default=None,
                      help="Specifies the upload rate of the client (KB/s).")
    
    parser.add_option("-y", "--download",
                      action="store", type="int", dest="download", 
                      default=None,
                      help="Specifies the download rate of the client (KB/s).")
    
    parser.add_option("-s", "--single_torrent",
                      action="store", dest="single_torrent",
                      default=None,
                      help="If you want to pass a specific torrent file into the client " + \
                      "you should use this option. Please note that if you specify a " + \
                      "single torrent, the client will not start the other " + \
                      "torrents which reside in its download directory.")
    
    parser.add_option("-r", "--report_to",
                      action="store", dest="report_to",
                      default=None,
                      help="Describes an URI to which the client shall report to.")
    
    parser.add_option("-c", "--config",
                      action="store", dest="config",
                      default=None,
                      help="Locates the file with unique configurations for all clients in a testbed.")
    
    parser.add_option("-e", "--stop",
                      action="callback", dest="exit", callback=_parse_stop_option,
                      #default=0,
                      help="Specifies the amount of time that a client will be running after all downloads finished.")
    
    parser.add_option("-I", "--I",
                      action="store", dest="ip_prefix", default=None,
                      help="The client only accepts connections to other clients if their IP addresses match the prefix of the given IP. The IP prefix must be given in network format, e.g. \"127.0.0.1/32\"")
    
    parser.add_option("-A", "--activity_report_interval", type="int",
                      action="store", dest="activity_report_interval",
                      default=None, help="Specifies the amount of time between the sending of two activity reports (only for the IoP case!). If this is 0, no reports will be send.")

    parser.add_option("-D", "--delete_directories", action="store_true", dest="delete_directories",
                      default=None, help="Triggers the removal of directories after the client has " +
                      "finished.")
    
    parser.add_option("-H", "--enable_hap", action="store_true", dest="hap_enabled",
                      default=None, help="Enables HAP support.")
    
    parser.add_option("-T", "--hap_interval", action="store", dest="hap_interval", type="int",
                      default=None, help="Defines the time in seconds between two succesive HAP reports.")
    
    parser.add_option("-S", "--supporter_seed", action="store_true", dest="is_supporter_seed",
                      default=False, help="Acts as supporter seed.")
    
    (options, args) = parser.parse_args(cl)
    

#    
#    # the user specified a custom directory for the client if the value
#    # in options.directory does not equal the value in the global variable
#    # directory
#    if options.directory:
#        # user specified a download directory, so validate it
#        if not options.directory.endswith(os.path.normcase('/')):
#            options.directory += os.path.normcase('/')
#        # check if the directory is present in the file system
#        # if not, create it
#        if not os.access(options.directory, os.F_OK):
#            os.mkdir(options.directory)
#    elif options.directory is None:
#        # the user specified no download directory, so we need to create
#        # one using tempfile.mkdtemp(). this directory is only assumed to be
#        # of temporary state, so we will delete it without further notice
#        # after the execution of this script
#        options.directory = tempfile.mkdtemp()
#        temp_dirs.append(options.directory)
#        
#    # them same holds for the state directory
#    if options.temporary_state_directory:
#        if not options.temporary_state_directory.endswith(os.path.normcase('/')):
#            options.temporary_state_directory += os.path.normcase('/')
#        if not os.access(options.temporary_state_directory, os.F_OK):
#            #os.mkdir(options.temporary_state_directory, os.F_OK)
#            os.mkdir(options.temporary_state_directory)
#    elif options.temporary_state_directory is None:
#        options.temporary_state_directory = tempfile.mkdtemp()
#        temp_dirs.append(options.temporary_state_directory)
#        
#    # check if the single torrent (if you provided it) is present
#    if options.singleTorrent is not None:
#        if not os.access(options.singleTorrent, os.F_OK):
#            parser.error("The torrent file you specified does not exist.")
#            sys.exit()
#    
#    # check if the directory in which the logfile shall be stored is
#    # present in the filesystem. if not, create it
#    if options.logfile is not None:
#        logfileDirectory = FileUtils.get_path_from_full_filename(options.logfile)
#        if options.logfile.find('/') >-1 and not os.access(logfileDirectory, os.F_OK):
#            os.mkdir(logfileDirectory)
        
    return (options, args)

def _parse_stop_option(option, opt_str, value, parser):
    assert value is None
    value = []
    
    def floatable(str):
        try:
            float(str)
            return True
        except ValueError:
            return False
    
    for arg in parser.rargs:
        if arg[:2] == "--" and len(arg) > 2:
            break
        if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
            break
        value.append(arg)
        
    del parser.rargs[:len(value)]
    setattr(parser.values, option.dest, value)
