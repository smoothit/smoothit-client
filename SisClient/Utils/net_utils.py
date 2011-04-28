import socket
import fcntl
import struct

def get_own_ip_addr(iface="eth0"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                            0x8915,
                                            struct.pack('256s', iface[:15]))[20:24])
        return addr
    except:
        # if anything goes wrong, return the default address for this host
        # (should be the loopback interface if not configured properly)
        return socket.gethostbyaddr(socket.gethostname())[2][0]