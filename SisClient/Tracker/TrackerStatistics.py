import time

class TrackerStatistics(object):
    # dict with key = peer_id that references dict with keys in
    # ['ip', 'port']
    _peers = {}
    # dict with key = infohash that references dict with key 'id'
    # 'id' references a another dict with keys in
    # ['arrival', 'completed', 'departure', 'uploaded', 'downloaded']
    # where uploaded and downloaded is a list of 2-tuples of the form
    # (ts, size)
    _torrents = {}
    # write received data to an output file
    _out = open('trackerstatistics.out', 'w')
    
    def __init__(self, tracker):
        self._tracker = tracker
        
    def __del__(self):
        if self._out is not None:
            self._out.close()
        
    def _add_torrent_entry(self, infohash, data):
        self._torrents[infohash] = {}
        
    def _add_torrent_peer_entry(self, infohash, data):
        ts = time.time()
        self._torrents[infohash][data['id']] = {
                'arrival' : ts,
                'completed' : -1,
                'departure' : -1,
                'uploaded' : [],
                'downloaded' : [] }
        
    def _add_peer_entry(self, data):
        self._peers[id] = { 'id'    :   data['id'],
                            'ip'    :   data['ip'],
                            'port'  :   data['port'] }
        
    def _extract_data(self, event, paramslist, ip):
        def params(key, default=None, l=paramslist):
            if l.has_key(key):
                return l[key][0]
            return default
        
        data = {}
        # gather attributes of paramslist
        data['id'] = params('peer_id')
        data['port'] = long(params('port'))
        data['uploaded'] = long(params('uploaded', ''))
        data['downloaded'] = long(params('downloaded', ''))
        data['left'] = long(params('left',''))
        data['event'] = event
        data['ip'] = ip
        
        if len(data['id']) != 20:
            raise ValueError, 'id not of length 20'
        if data['port'] < 0 or data['port'] > 65535:
            raise ValueError, 'invalid port'
        if data['left'] < 0:
            raise ValueError, 'invalid amount left'
        if data['event'] not in ['started', 'completed', 'stopped', 'snooped', None]:
            raise ValueError, 'invalid event'
        
        return data
    
    def _set_event_time_from_event(self, infohash, data):
        if data['event'] == 'stopped':
            self._torrents[infohash][data['id']]['departure'] = time.time()
        elif data['event'] == 'completed':
            self._torrents[infohash][data['id']]['completed'] = time.time()
        
    def _add_utilization_data(self, infohash, data):
        ts = time.time()
        self._torrents[infohash][data['id']]['uploaded'].append((ts, data['uploaded']))
        self._torrents[infohash][data['id']]['downloaded'].append((ts, data['downloaded']))
        
    def _write_dataline_to_out(self, infohash, data):
        line = "%i: %s\t%s:%s\t%s\t%s\t%d\t%d\t%d\t%s\t%s" % (
                                    time.time(),
                                    data['id'],
                                    data['ip'],
                                    str(data['port']),
                                    data['event'],
                                    self._tracker.allowed[infohash]['name'],
                                    self._torrents[infohash][data['id']]['arrival'],
                                    self._torrents[infohash][data['id']]['completed'],
                                    self._torrents[infohash][data['id']]['departure'],
                                    data['uploaded'],
                                    data['downloaded'])
        self._out.write(line)
        self._out.write('\n')
        self._out.flush()
    
    def on_data(self, infohash, event, ip, paramslist):
        data = self._extract_data(event, paramslist, ip)
        if not self._peers.has_key(data['id']):
            self._add_peer_entry(data)
        if not self._torrents.has_key(infohash):
            self._add_torrent_entry(infohash, data)
        if not self._torrents[infohash].has_key(data['id']):
            self._add_torrent_peer_entry(infohash, data)
        self._set_event_time_from_event(infohash, data)
        self._add_utilization_data(infohash, data)
        self._write_dataline_to_out(infohash, data)