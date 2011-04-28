import optparse

def parse_cache_options(cl):
    assert type(cl) == list
    parser = optparse.OptionParser()
    
    parser.add_option("-p", "--port", 
                      action="store", type="int", dest="port", default=None,
                      help="port that the cache should listen on for incomming \
                            connections.")    
    
    parser.add_option("-d", "--directory", 
                      action="store", dest=None,
                      help="directory to save files in.")
    
    parser.add_option("-t", "--torrentdir", 
                      action="store", dest="torrentdir", default=None,
                      help="directory to save torrents in.")
    
    parser.add_option("-x", "--downlimit", default=None,
                      action="store", type="int", dest="downlimit",
                      help="upload limit (KB/s).")
    
    parser.add_option("-y", "--uplimit", default=None,  
                      action="store", type="int", dest="uplimit",
                      help="donwload limit (KB/s).")
    
    parser.add_option("-s", "--spacelimit", 
                      action="store", type="int", dest="spacelimit", default=None,
                      help="disc space that the cache can use in MB (default: 100).")
    
    parser.add_option("-o", "--conlimit", 
                      action="store", type="int", dest="conlimit", default=None,
                      help="maximal connection that the cache should use (default: 10).")
    
    parser.add_option("-l", "--logfile", 
                      action="store", dest=None,
                      help="sets the destination of the log file.")
    
    parser.add_option("-i", "--id", 
                      action="store", type="int", dest="id", default = None,
                      help="id that identifies the cache in the local testbed (random by default).")
    
    parser.add_option("-b", "--ranking_source",
                      action="store", dest="ranking_source", default=None,
                      help="set the source and type of peer rankings operation mode of neighbor selection (none|samehost|geoip|odd_even|sis|sis_simple|ip_pre).\
                      Default is IP prefixes. IP prefixes itself can be configured via config file.")
    
    parser.add_option("-u", "--sis_url",
                      action="store", dest="sis_url", default=None,
                      help="Specifies the SIS url of the form 'http://<hostname>:<port>/sis'")#typical port: 8080
    
    parser.add_option("-r", "--report_to",
                      action="store", dest="report_to",
                      default=None,
                      help="Describes an URI to which the client shall report to.")
    
    parser.add_option("-c", "--config",
                      action="store", dest="config",
                      default=None,
                      help="Locates the file with unique configurations for all clients in a testbed.")
    parser.add_option("-C", "--console",
                      action="store_true", dest="cache_console",
                      default=False,
                      help="Enables the cache console to allow manual controls.")
    
    (options, args) = parser.parse_args(cl)

    return (options, args)