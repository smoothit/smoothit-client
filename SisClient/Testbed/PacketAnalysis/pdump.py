import optparse
import pcap
import sys
import string

from pcallback import PCAPBasicHandler

def parse_options():
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + \
                                   " <interface> [options]")
    parser.add_option("-f", "--filter",
                      action="store", dest="filter", default="",
                      help="Adda a a packet capture filter. See the tcpdump " + \
                      "manpage for more information about packet filters.")
    parser.add_option("-l", "--log",
                      action="store", dest="logfile", default="packets.log",
                      help="Specify a logfile to which packet data will be " + \
                      "written in addition to the standard output.")
    parser.add_option("-m", "--mode",
                      action="store", dest="mode", default="live",
                      help="Determines the execution mode of pdump. Available " + \
                      "modes are: live, offline")
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        print >>sys.stderr, "Missing required interface."
        parser.print_help()
        parser.exit(1)
        
    modes = ["live", "offline"]
    if options.mode.lower() not in modes:
        print >>sys.stderr, "Mode %s is not supported." % options.mode
        parser.print_help()
        parser.exit(1)
        
    return (options, args)

def run_offline(p):
    print "Starting packet capture to dumpfile..."
    file = "packets.dump"
    p.dump_open(file)
    try:
        while 1:
            p.dispatch(0, None)
    except KeyboardInterrupt:
        print "%s" % sys.exc_type
        print "stopping packet capture..."
        print "%d packets received, %d packets dropped, %d packets dropped by interface" % p.stats()
        sys.exit(0)

def run_live(p, filename):
    print "Starting live packet capture..."
    handler = PCAPBasicHandler(filename)
    
    try:
        while 1:
            packet = p.next()
            apply(handler.on_packet, packet)
    except KeyboardInterrupt:
        print "%s" % sys.exc_type
        print "stopping packet capture..."
        print "%d packets received, %d packets dropped, %d packets dropped by interface" % p.stats()
        sys.exit(0)                
        
def main():
    options, args = parse_options()
    
    p = pcap.pcapObject()
    device = sys.argv[1]
    net, mask = pcap.lookupnet(device)
    p.open_live(device, 1600, 0, 100)
    p.setfilter(options.filter, 0, 0)
    if options.mode.lower() == "offline":
        run_offline(p)
    else:
        run_live(p, options.logfile)

if __name__ == "__main__":
    main()