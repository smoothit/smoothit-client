import pcap
import socket
import struct

protocols = { socket.IPPROTO_TCP    :   'tcp',
              socket.IPPROTO_UDP    :   'udp',
              socket.IPPROTO_ICMP   :   'icmp'
}

convert_from_byte = { 'byte'    :   1,
                      'kb'      :   1024,
                      'mb'      :   1024*1024
}

def decode_ip_packet(s):
    '''decode_ip_packet was taken from the example implementations that
       came along with python-libpcap.'''
    d={}
    d['version']=(ord(s[0]) & 0xf0) >> 4
    d['header_len']=ord(s[0]) & 0x0f
    d['tos']=ord(s[1])
    d['total_len']=socket.ntohs(struct.unpack('H',s[2:4])[0])
    d['id']=socket.ntohs(struct.unpack('H',s[4:6])[0])
    d['flags']=(ord(s[6]) & 0xe0) >> 5
    d['fragment_offset']=socket.ntohs(struct.unpack('H',s[6:8])[0] & 0x1f)
    d['ttl']=ord(s[8])
    d['protocol']=ord(s[9])
    d['checksum']=socket.ntohs(struct.unpack('H',s[10:12])[0])
    d['source_address']=pcap.ntoa(struct.unpack('i',s[12:16])[0])
    d['destination_address']=pcap.ntoa(struct.unpack('i',s[16:20])[0])
    if d['header_len']>5:
        d['options']=s[20:4*(d['header_len']-5)]
    else:
        d['options']=None
    d['data']=s[4*d['header_len']:]
    return d

def detailed_packet_repr(decoded_packet, timestamp):
    dispatch = "%s.%f %s > %s" % (time.strftime('%H:%M', time.localtime(timestamp)),
                                   timestamp % 60,
                                   decoded_packet['source_address'],
                                   decoded_packet['destination_address'])
    return dispatch
