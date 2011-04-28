import os
import re
import sys

from subprocess import Popen

from BaseLib.Core.BitTornado import bencode

TEMPORARY_STDERR_FILE = "tmpstderrfile.ffmpeg"

def check_files(list_of_files):
    for file in list_of_files:
        if not os.access(file, os.F_OK):
            print >>sys.stderr, "File %s is not accessable." % file
            sys.exit(1)
            
def videostats_via_ffmpeg(filename):
    def _create_matcher():
        pattern = "[A-Za-z/._:]* bitrate: ([0-9]*) [A-Za-z/._]"
        matcher = re.compile(pattern)
        return matcher
    
    def extract_duration(line):
        pattern = "[A-Za-z/._:]* Duration: ([A-Za-z0-9/_:]*).[0-9]*, [A-Za-z0-9/._]*"
        matcher = re.compile(pattern)
        result = matcher.findall(line)
        return result[0]
    
    matcher = _create_matcher()
    # create a file handle to which we redirect the stderr output
    stderrhandle = open(TEMPORARY_STDERR_FILE, "w")
    # open a child process that runs ffmpeg
    child = Popen("ffmpeg -i '%s'" % filename, shell=True, stderr=stderrhandle)
    child.wait()
    stderrhandle.close()
    # information on the video file is now stored in the temporary file.
    # open the file, parse it line by line and match each line against the
    # regular expression we defined in _create_matcher.
    stderrhandle = open(TEMPORARY_STDERR_FILE, "r")
    videostats = {}
    try:
        for line in stderrhandle.readlines():
            parsed = matcher.findall(line)
            if len(parsed) > 0:
                # the line matches, now return the bitrate in b/s as an int
                # the '* 1024 / 8' is needed, since ffmpeg prints the bitrate
                # in kb/s, but we need it in byte/s
                #videostats['bitrate'] = int(parsed[0]) * 1024 / 8
                duration = extract_duration(line)
                tokens = duration.split(':')
                #videostats['playtime'] = int(tokens[0])*60*60 + int(tokens[1])*60 + int(tokens[2])
                videostats['playtime'] = duration
                return videostats
    finally:
        # close the file handle and delete the temporary file
        stderrhandle.close()
        os.unlink(TEMPORARY_STDERR_FILE)

#___________________________________________________________________________________________________
# MAIN

def main():
    args = sys.argv[1:]
    if len(sys.argv[1:]) != 2:
        print >>sys.stderr, "Usage: %s <torrent> <file>" % sys.argv[0]
        sys.exit(1)
    
    check_files([args[0], args[1]])
    videostats = videostats_via_ffmpeg(args[1])
    print "Reading torrent metainfo..."
    metainfo_fhandle = open(args[0], 'rb')
    metainfo = bencode.bdecode(metainfo_fhandle.read())
    metainfo_fhandle.close()
    metainfo['playtime'] = videostats['playtime']
    print "Encoding new torrent metainfo..."
    metainfo_fhandle = open(args[0]+'-new', 'wb')
    b = bencode.bencode(metainfo)
    metainfo_fhandle.write(b)
    metainfo_fhandle.close()
    print "New torrent metainfo written to file %s" % (args[0]+'-new')

if __name__ == "__main__":
    main()
