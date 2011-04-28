import os
import putil
import pygeoip

class PCAPCallbackHandler():
    def __init__(self):
        pass
    
    def on_packet(self, pktlen, data, timestamp):
        pass
    
class PCAPBasicHandler(PCAPCallbackHandler):
    _out = None
    
    def __init__(self, filename):
        self._out = open(filename, 'w')
        
    def __del__(self):
        if self._out is not None:
            self._out.close()
    
    def on_packet(self, pktlen, data, timestamp):
        if not data:
            return
        
        decoded_packet = putil.decode_ip_packet(data[14:])
        outstr = "%d\t%s\t%s\t%d" % (timestamp,
                                     decoded_packet['source_address'],
                                     decoded_packet['destination_address'],
                                     decoded_packet['total_len'])
        print outstr
        self._out.write(outstr)
        self._out.write('\n')
    
class PCAPAnalyzerHandler(PCAPCallbackHandler):
    
    _intra_packets_size = long(0)
    _inter_packets_size = long(0)
    _interval = 60
    _last_seen_ts = 0
    _interval_start = -1
    #_gi = pygeoip.GeoIP('resources/GeoLiteCity.dat')
    _out = None
    
    def __init__(self, filename, interval=60):
        self._interval = interval
        self._out = open(filename, 'w')
        
    def __del__(self):
        if self._out is not None:
            self._out.close()
    
    def on_packet(self, pktlen, data, timestamp):
        if not data:
            return
    
        self._last_seen_ts = timestamp
        if self._interval_start == -1:
            self._interval_start = timestamp
    
        if data[12:14] == '\x08\x00':
            decoded_packet = putil.decode_ip_packet(data[14:])
        
            # check if both source and destination address are in the same domain
            sa_dict = self._gi.record_by_addr(decoded_packet['source_address'])
            da_dict = self._gi.record_by_addr(decoded_packet['destination_address'])
            
            if sa_dict is not None and da_dict is not None and sa_dict.has_key('city') and da_dict.has_key('city'):
                if sa_dict['city'] == da_dict['city']:
                    # we count this as intradomain traffic
                    self._intra_packets_size += decoded_packet['total_len']
                else:
                    # we count this as interdomain traffic
                    self._inter_packets_size += decoded_packet['total_len']
            
                    print "ts: %d\tsource: %s\t\tdestination: %s" % (timestamp,
                                                                     decoded_packet['source_address'],
                                                                     decoded_packet['destination_address'])
    
        if (timestamp - self._interval_start) >= self._interval:
            self.write_to_file(timestamp)

    def write_to_file(self, timestamp=None):
        if timestamp is None:
            timestamp = self._last_seen_ts
        self._interval_start = timestamp
        outstr = "%d\t%d\t%d" % (timestamp,
                                 self._inter_packets_size,
                                 self._intra_packets_size)
        self._out.write(outstr)
        self._out.write('\n')
        self._inter_packets_size = long(0)
        self._intra_packets_size = long(0)