import optparse
import os
import re
import subprocess
import sys
import tempfile
import time
import utils
import urllib2

from subprocess import Popen
from BaseLib.Core.API import *

TEMPORARY_STDERR_FILE = "tmpstderrfile.bitrate"
PIECESIZE = 32768

def _parse_options():
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + " [options] <videofile>")
    
    parser.add_option("-n", "--name",
                      action="store", dest="name", default="",
                      help="name of the stream.")
    parser.add_option("-u", "--tracker_url",
                      action="store", dest="url",
                      default="http://localhost:8859/announce",
                      help="the tracker url has to follow the pattern: " +
                      "http://url:port/announce")
    parser.add_option("-t", "--tracker_time",
                      action="store", type="int", dest="timeout",
                      default=10,
                      help="the amount of time the tracker has to create the " +
                      "torrent file")
    
    options, args = parser.parse_args()
    
    if len(args) != 1:
        parser.error("Video file name is missing.")
        parser.print_help()
        sys.exit(-1)
        
    if not utils.verify_tracker_url(options.url):
        parser.error("The tracker URL must follow the pattern: " +
                     "http://tracker-url:port/announce")
        parser.print_help()
        sys.exit(-1)
        
    if not os.path.exists(args[0]):
        parser.error("The videofile %s does not exist." % args[0])
        parser.print_help()
        sys.exit(-1)
        
    if options.name == "":
        # if no stream name is given, take the filename for it
        options.name = args[0]
        
    return options, args

def _create_matcher():
    pattern = "[A-Za-z/._:]* bitrate: ([0-9]*) [A-Za-z/._]"
    matcher = re.compile(pattern)
    return matcher

def extract_duration(line):
    pattern = "[A-Za-z/._:]* Duration: ([A-Za-z0-9/_:]*).[0-9]*, [A-Za-z0-9/._]*"
    matcher = re.compile(pattern)
    result = matcher.findall(line)
    return result[0]

def bitrate_via_ffmpeg(filename):
    matcher = _create_matcher()
    # create a file handle to which we redirect the stderr output
    stderrhandle = open(TEMPORARY_STDERR_FILE, "w")
    # open a child process that runs ffmpeg
    child = Popen("ffmpeg -i %s" % filename, shell=True, stderr=stderrhandle)
    child.wait()
    stderrhandle.close()
    # information on the video file is now stored in the temporary file.
    # open the file, parse it line by line and match each line against the
    # regular expression we defined in _create_matcher.
    stderrhandle = open(TEMPORARY_STDERR_FILE, "r")
    try:
        for line in stderrhandle.readlines():
            parsed = matcher.findall(line)
            if len(parsed) > 0:
                # the line matches, now return the bitrate in b/s as an int
                # the '* 1024 / 8' is needed, since ffmpeg prints the bitrate
                # in kb/s, but we need it in byte/s
                bitrate_in_byte = int(parsed[0]) * 1024 / 8
                duration = extract_duration(line)
                return bitrate_in_byte, duration
    finally:
        # close the file handle and delete the temporary file
        stderrhandle.close()
        os.unlink(TEMPORARY_STDERR_FILE)
        
def create_livestream_torrent(filename, options):
    statedir = tempfile.mkdtemp()
    
    port = utils.extract_tracker_port_from_url(options.url)
    bitrate, duration = bitrate_via_ffmpeg(filename)
    sscfg = SessionStartupConfig()
    sscfg.set_state_dir(statedir)
    sscfg.set_listen_port(port)
    sscfg.set_megacache(False)
    sscfg.set_overlay(False)
    sscfg.set_dialback(True)
    
    session = Session(sscfg)
    
    tdef = TorrentDef()
    tdef.create_live(filename, bitrate, duration)
    tdef.set_tracker(session.get_internal_tracker_url())
    tdef.set_piece_length(PIECESIZE)
    tdef.finalize()
    tdef.save(options.name + ".tstream")
    
    dscfg = DownloadStartupConfig()
    dscfg.set_dest_dir(".")
    
    # the streaming source is a local file
    source = open(filename, "rb")
    dscfg.set_video_ratelimit(tdef.get_bitrate())   
    dscfg.set_video_source(source)
    
    d = session.start_download(tdef, dscfg)
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        _cleanup(session, statedir)
        sys.exit()
        
def _cleanup(session, statedir):
    session.shutdown()
    # give the session some time to properly perform the shutdown
    time.sleep(3)
    # remove the temporary state directory
    utils.FileUtils.remove_directory_recursively(statedir)
    
#_______________________________________________________________________________
# MAIN

if __name__ == "__main__":
    options, args = _parse_options()
    create_livestream_torrent(args[0], options)