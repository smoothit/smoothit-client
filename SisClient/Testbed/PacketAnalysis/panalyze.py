import pcap
import sys
import putil
import optparse
import os

from pcallback import PCAPAnalyzerHandler

options = None
args = None
    
def parse_options():
    global options, args
    
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + \
                                   " <dumpfile> <outputfile> [options]")
    parser.add_option("-i", "--interval",
                      action="store", type="int", dest="interval", default="30",
                      help="Defines the time in seconds after which an log entry " + \
                      "will be written to the output file.")
    parser.add_option("-u", "--unit",
                      action="store", dest="unit", default="byte",
                      help="Converts the output of packet sizes to the " + \
                      "specified unit, where unit is in (byte, kb, mb).")
    (options, args) = parser.parse_args()
    
    if len(args) != 2:
        parser.print_help()
        parser.exit(1)
    
    if not os.access(args[0], os.F_OK):
        parser.error("The dumpfile is not accessible or it does not exist.")
        parser.exit(1)
#_______________________________________________________________________________
# MAIN

def main():
    global options, args, output_handle
    
    parse_options()
    p = pcap.pcapObject()
    p.open_offline(args[0])
    output_handle = open(args[1], 'w')
    
    handler = PCAPAnalyzerHandler(args[1], options.interval)
    
    try:
        while 1:
            packet = p.next()
            if packet is None:
                print "analyzing finished..."
                handler.write_to_file()
                output_handle.close()
                sys.exit(0)
            apply(handler.on_packet, packet)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()