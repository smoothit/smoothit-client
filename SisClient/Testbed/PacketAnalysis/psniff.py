import sys
import pcap
import string
import time
import socket
import struct
import optparse
import os
import putil

__author__ = "Markus Guenther"

protocols = { socket.IPPROTO_TCP    :   'tcp',
              socket.IPPROTO_UDP    :   'udp',
              socket.IPPROTO_ICMP   :   'icmp'
}

convert_from_byte = { 'byte'    :   1,
                      'kb'      :   1024,
                      'mb'      :   1024*1024
}

options = None
args = None
total_packets_size = long(0)
total_packets_recv = long(0)
logfile_handle = None

#_______________________________________________________________________________
# FUNCTIONS

def detailed_packet_repr(decoded_packet, timestamp):
    dispatch = "%s.%f %s > %s" % (time.strftime('%H:%M', time.localtime(timestamp)),
                                   timestamp % 60,
                                   decoded_packet['source_address'],
                                   decoded_packet['destination_address'])
    return dispatch
    
def on_packet(pktlen, data, timestamp):
    global options
    global total_packets_recv
    global total_packets_size
    
    if not data:
        return
    
    if data[12:14] == '\x08\x00':
        decoded_packet = putil.decode_ip_packet(data[14:])
        # update global statistics
        total_packets_recv += 1
        total_packets_size += decoded_packet['total_len']        
        
        print_decoded_packet(decoded_packet, 
                             timestamp, 
                             options.logfile is not None)
    
def print_decoded_packet(decoded_packet, timestamp, dump_to_file=False):
    global options
    global total_packets_recv
    global total_packets_size
    global convert_from_byte
    global logfile_handle
    
    # basic information
    output_string = "total packet size: %d %s\t\ttotal amount of recv packets: %d" \
          % (total_packets_size / convert_from_byte[options.convert_from_byte],
             options.convert_from_byte,
             total_packets_recv)
    print output_string
    if logfile_handle is not None:
        logfile_handle.write(output_string)
        logfile_handle.write('\n')
    
    if options.verbose_mode:
        # generate detailed information and write it to stdout
        details = detailed_packet_repr(decoded_packet, timestamp)
        print details
        if dump_to_file and logfile_handle is not None:
            logfile_handle.write(details)
            logfile_handle.write('\n')
            
def on_shutdown(signal=None, func=None):
    global logfile_handle
    
    print "shutting down..."
    # close open file handles
    if logfile_handle is not None:
        logfile_handle.close()
        
#_______________________________________________________________________________
# UTILITY FUNCTIONS
        
def set_exit_handler(func):
    '''Allows to set an exit handler that gets called if the running Python
    process gets killed. This can be used to clean up after the application
    has exited. The behaviour on a Windows system is a bit different.
    If you kill the Python process via the Task Manager, you will not get
    a chance to run additional cleanup code.'''
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception ("pywin32 not installed for Python " + version)
    else:
        import signal
        signal.signal(signal.SIGTERM, func)
            
def parse_options():
    global options
    global args
    global convert_from_byte
    
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + \
                                   " <interface> [options]")
    parser.add_option("-f", "--filter",
                      action="store", dest="filter", default="",
                      help="Adda a a packet capture filter. See the tcpdump " + \
                      "manpage for more information about packet filters.")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose_mode", default=False,
                      help="Prints out packet information as well.")
    parser.add_option("-l", "--log",
                      action="store", dest="logfile", default=None,
                      help="Specify a logfile to which packet data will be " + \
                      "written in addition to the standard output.")
    parser.add_option("-u", "--unit",
                      action="store", dest="convert_from_byte", default="byte",
                      help="Converts the output of packet sizes to the specified " + \
                      "unit, where unit is in (byte, kb, mb).")
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.print_help()
        parser.exit(1)
        
    if options.convert_from_byte not in convert_from_byte.keys():
        parser.print_help()
        parser.exit(1)

#_______________________________________________________________________________
# MAIN

def main():
    global options
    global args
    global logfile_handle
    
    parse_options()
    set_exit_handler(on_shutdown)
    
    if options.logfile is not None:
        # open file handle
        logfile_handle = open(options.logfile, 'w')
    
    p = pcap.pcapObject()
    device = args[0]
    net, mask = pcap.lookupnet(device)
    p.open_live(device, 1600, 0, 100)
    p.setfilter(options.filter, 0, 0)

    try:
        while 1:
            p.dispatch(1, on_packet)
    except KeyboardInterrupt:
        on_shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()