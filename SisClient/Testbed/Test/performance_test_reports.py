import optparse
import sys
import zipfile
import re
import random
import os
import urllib
import threading
import time

# symbolic constants (default values)
FEW_NEIGHBOURS, MANY_NEIGHBOURS = ("reports_small.zip", "reports_large.zip")
REQUEST_INTERVAL = 1
IS_RUNNING = True
VERBOSE = False
NO_REQUESTS = 0
TOTAL_SIZE = 0

def get_random_xml_report(handle):
    pattern = "[A-Za-z/._]*.xml"
    matcher = re.compile(pattern)
    
    lopf = []
    for filename in handle.namelist():
        if len(matcher.findall(filename)) > 0:
            lopf.append(filename)
    
    if len(lopf) == 0:
        print >>sys.stderr, "The given ZIP file does not contain XML reports."
        sys.exit(1)
        
    idx = random.randint(0, len(lopf)-1)
    return handle.read(lopf[idx])

def send_request_to_server(handle, options):
    global IS_RUNNING
    global NO_REQUESTS
    global TOTAL_SIZE
    
    if not IS_RUNNING:
        return
    
    data = get_random_xml_report(handle)
    size = len(data)
    log("Sending request with size %d Bytes to server." % size)
    TOTAL_SIZE += size
    urlhandle = urllib.urlopen(options.url, data)
    result = urlhandle.read()
    urlhandle.close()
    NO_REQUESTS += 1
    create_request_timer(handle, options)
    
def create_request_timer(handle, options):
    if not IS_RUNNING:
        return
    timer = threading.Timer(options.interval, send_request_to_server,
                            [handle, options])
    timer.start()
    log("Started new request thread.")

def exit_script():
    global IS_RUNNING
    print >>sys.stdout, "Finished test..."
    IS_RUNNING = False
    
def log(text):
    global VERBOSE
    if VERBOSE:
        print >>sys.stdout, "%i: %s" % (time.time(), text)
        
def summarize(options):
    global NO_REQUESTS
    log("Sent %i XML reports to the server." % NO_REQUESTS)
    log("Total size of XML data sent to server: %i Bytes" % TOTAL_SIZE)
    log("Total running time was %i seconds." % options.timeout)

def start_test(options):
    log("Starting the stresstest...")
    handle = None
    if options.neighbours == "few":
        log("Opening %s." % FEW_NEIGHBOURS)
        handle = zipfile.ZipFile(FEW_NEIGHBOURS, "r")
    else:
        log("Opening %s." % MANY_NEIGHBOURS)
        handle = zipfile.ZipFile(MANY_NEIGHBOURS, "r")
    
    exit_timer = threading.Timer(options.timeout, exit_script)
    exit_timer.start()
    create_request_timer(handle, options)
    while IS_RUNNING:
        try:
            pass
        except KeyboardInterrupt:
            summarize(options)
            handle.close()
            os._exit(0)
    summarize(options)
    handle.close()
    os._exit(0)

def parse_options():
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + " [options]",
                                   description="This script will send a vast " + \
                                   "amount of pre-generated reports to a " + \
                                   "statistics server.")
    
    parser.add_option("-u", "--url",
                      action="store", dest="url", default="http://localhost:8888",
                      help="URL of the statistics server. Defaults to " + \
                      "http://localhost:8888")
    parser.add_option("-n", "--neighbour_set",
                      action="store", dest="neighbours", default="few",
                      help="Determines the size of the neighbour set. The options " + \
                      "here are: \"few\" | \"large\". Defaults to \"few\"")
    parser.add_option("-i", "--interval",
                      action="store", dest="interval", default=REQUEST_INTERVAL,
                      help="Time interval in seconds that needs to pass before " + \
                      "a subsequent request will be send to the server. " + \
                      "Defaults to 1.", type="int")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="The scripts write some information on the testing " + \
                      "testing process to stdout. By default not active.")
    parser.add_option("-r", "--running_time",
                      action="store", dest="timeout", default=60, type="int",
                      help="Specifies the running time of the script in seconds. " + \
                      "Defaults to 60 seconds.")
    
    return parser.parse_args()

#_______________________________________________________________________________
# MAIN

def main():
    global VERBOSE
    
    if not os.access(FEW_NEIGHBOURS, os.F_OK):
        print >>sys.stderr, "ZIP file containing reports with few neighbours is missing."
        sys.exit(1)
        
    if not os.access(MANY_NEIGHBOURS, os.F_OK):
        print >>sys.stderr, "ZIP file containing reports with many neighbours is missing."
        sys.exit(1)
    
    options, args = parse_options()
    
    if options.neighbours not in ["few", "large"]:
        print >>sys.stderr, "Please specify the neighbour set correctly. Given: %s" % options.neighbours
        sys.exit(1)
        
    VERBOSE = options.verbose
    
    start_test(options)

if __name__ == "__main__":
    main()