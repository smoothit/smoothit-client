import sys
import time
import os
import optparse
import math
import tempfile
import urllib
import logging
import logging.config

from BaseLib.Core.SessionConfig import SessionStartupConfig
from BaseLib.Core.Session import Session
from BaseLib.Core import simpledefs
from BaseLib.Core.TorrentDef import TorrentDef
from BaseLib.Core.DownloadConfig import DownloadStartupConfig
from traceback import print_exc

import SisClient.Utils.common_utils as utils

EVENT_RESOLUTION = { simpledefs.VODEVENT_PAUSE  :   'VODEVENT_PAUSE',
                     simpledefs.VODEVENT_RESUME :   'VODEVENT_RESUME',
                     simpledefs.VODEVENT_START  :   'VODEVENT_PLAY' }

client_stats = { 'is_playing'           :   False,
                 'played'               :   0,
                 'dropped'              :   0,
                 'stall'                :   0,
                 'prebuf'               :   0,
                 'late'                 :   0,
                 'last_seen_pause_at'   :   None,
                 'stall_time'           :   0.0,
                 'ts_started'           :   time.time(),
                 'ts_playback_started'  :   None,
                 'ts_playback_ended'    :   None,
                 'calculated_stall_time':   None,
                 'playback_duration'    :   None,
                 'video_duration'       :   None }

#___________________________________________________________________________________________________

class TrackerCommunicator(object):
    def __init__(self, tracker_url, own_port, peer_id):
        self._tracker_url = tracker_url
        self._own_port = own_port
        # torrent infohash is stored in hexadecimal representation, thus ensuring correct
        # transmission to the tracker extension (it must be converted back to binary there)
        self._peer_id = peer_id
        self._need_support = False
        
    def get_peer_id(self):
        return self._peer_id
    
    def send_registration(self):
        try:
            urllib.urlopen("%sregister_peer?port=%i&id=%s" % (self._tracker_url, self._own_port,
                                                                self._peer_id))
        except:
            print_exc()
    
    def send_support_required(self):
        #print >>sys.stderr, "send_support_required called, send msg to %s" % self._tracker_url
        if self._need_support is False:
            # new request cycle starts, so register the peer
            self.send_registration()
        try:
            urllib.urlopen("%srequest_support?id=%s" % (self._tracker_url, self._peer_id))
            self._need_support = True
        except:
            print_exc()
    
    def send_support_not_required(self):
        #print >>sys.stderr, "send_support_not_required called"
        if self._need_support: # tracker still thinks we need support
            # keeping state allows us to only send the abort message once
            try:
                urllib.urlopen("%sabort_support?id=%s" % (self._tracker_url, self._peer_id))
                self._need_support = False
            except:
                print_exc()
            
#___________________________________________________________________________________________________
# CALLBACK HANDLERS

def vod_event_callback(d, event, params):
    global BITRATE, client_stats
    #d.sd.dow.encoder.set_coordinator_ip("127.0.0.1")
    event_ts = time.time()
    
    print >>sys.stderr, "Got VOD Event: %s" % EVENT_RESOLUTION[event]

    if event == simpledefs.VODEVENT_START:
        if not params['stream']:
            print >>sys.stderr, 'Error: There is no stream handle. Closing session.'
            return
        
        content_length = d.get_def().get_length()
        
        stream = params['stream']
        grandtotal = 0L
        client_stats['is_playing'] = True
        client_stats['ts_playback_started'] = event_ts
        while True:
            total = 0
            while total < int(BITRATE):
                data = stream.read(int(BITRATE-total))
                total += len(data)
                
            grandtotal += total
            time.sleep(1)       
            done = int(math.ceil(float(grandtotal) / float(content_length) * 100))
            print >>sys.stderr, 'VodClient: PLAYBACK PROGRESS: %i%%' % done
            
            if done >= 100:
                print >>sys.stdout, 'Playback done. Shutting down session.'
                client_stats['ts_playback_ended'] = time.time()
                exit_handler()
                            
    elif event == simpledefs.VODEVENT_PAUSE:
        client_stats['last_seen_pause_at'] = event_ts
    
    elif event == simpledefs.VODEVENT_RESUME:
        client_stats['stall_time'] += (event_ts - client_stats['last_seen_pause_at'])

def state_event_callback(ds):
    def update_value(source_dict, target_dict, key):
        if source_dict.has_key(key) and target_dict.has_key(key):
            target_dict[key] = source_dict[key]
    
    global client_stats, communicator
    
    if ds.get_status() <= simpledefs.DLSTATUS_HASHCHECKING: 
        # don't send anything before we actually started the download
        return (1.0, True)
    
    if client_stats['is_playing']:
        v = ds.get_vod_stats()
        
        update_value(v, client_stats, 'played')
        update_value(v, client_stats, 'stall')
        update_value(v, client_stats, 'late')
        update_value(v, client_stats, 'dropped')
        update_value(v, client_stats, 'prebuf')
    

        
    bt1download = ds.get_download().sd.dow
    voddl = bt1download.voddownload
    storagewrapper = bt1download.storagewrapper
    
    support_required = False
    if voddl is not None:
        left,right = voddl.videostatus.get_high_range()
        
        not_have = 0
        for i in xrange(left,right+1):
            if not storagewrapper.do_I_have(i):
                not_have += 1
        
        support_required = (not client_stats['is_playing']) or not_have>0
        bt1download.update_support_required(support_required) 
        if support_required > 0:
            # our high prio set is not full yet, so request support
            communicator.send_support_required()
        else:
            communicator.send_support_not_required()
    
    print >>sys.stderr, "VodClient: DOWNLOAD PROGRESS: %i%%, playing=%s, support_required=%s" % (int(100.0 * ds.get_progress()), client_stats['is_playing'], support_required)
    
    #print >>sys.stderr, "New Block stats %s " % ds.get_block_stats()
    
    return (1.0, True)

def exit_handler():
    global client_stats
    
    client_stats['playback_duration'] = client_stats['ts_playback_ended'] - \
                                        client_stats['ts_playback_started']
    client_stats['calculated_stall_time'] = client_stats['ts_playback_ended'] - \
                                            client_stats['ts_playback_started'] - \
                                            client_stats['video_duration']
    client_stats['playback_delay_in_seconds'] = client_stats['ts_playback_started'] - \
                                                client_stats['ts_started']
    
    print_stats()
    os._exit(0)

def print_stats():
    global client_stats
    
    fhandle = open(__LOGFILE__, 'w')
    for key in client_stats.keys():
        outstr = '%s: %s\n' % (key, str(client_stats[key]))
        fhandle.write(outstr)
        print >>sys.stderr, "client_stats['%s']: %s" % (key, str(client_stats[key]))
    fhandle.close()

#___________________________________________________________________________________________________
# MAIN
if __name__ == "__main__":
    logging.config.fileConfig("config/log_client.conf")
    parser = optparse.OptionParser(usage="Usage: " + sys.argv[0] + " [options]")
    parser.add_option("-d", "--directory", dest="directory", default="vodclient")
    parser.add_option("-p", "--port", type="int", dest="port", default=5000)
    parser.add_option("-t", "--torrent", dest="torrent", default=None)
    parser.add_option("-x", "--dlrate", type="int", dest="dlrate", default=128)
    parser.add_option("-y", "--ulrate", type="int", dest="ulrate", default=128)
    parser.add_option("-l", "--logfile", dest="logfile", default=None)

    (options, args) = parser.parse_args()

    print >>sys.stderr, "download rate is: %i" % options.dlrate
    
    __TORRENT_FILE__ = options.torrent
    __LOGFILE__ = options.logfile or 'vodclient.log'

    scfg = SessionStartupConfig()
    scfg.set_state_dir(tempfile.mkdtemp())
    scfg.set_listen_port(options.port)
    scfg.set_overlay(False)
    scfg.set_megacache(False)
    scfg.set_upnp_mode(simpledefs.UPNPMODE_DISABLED)
    scfg.set_dialback(False)
    scfg.set_social_networking(False)
    scfg.set_buddycast(False)
    scfg.set_crawler(False)
    scfg.set_internal_tracker(False)

    s = Session(scfg)

    tdef = TorrentDef.load(__TORRENT_FILE__)
# tdef.get_tracker() returns the announce-url; we must omit the "announce" part
    tracker_url = tdef.get_tracker()[:tdef.get_tracker().find("announce")]

    if tdef.get_bitrate() == None:
        print >>sys.stderr, "Provided torrent file has no bitrate information. Exiting."
        sys.exit(1)

    BITRATE = tdef.get_bitrate()
    print >>sys.stderr, "Calculated bitrate is %d" % BITRATE
    client_stats['video_duration'] = int(tdef.get_length() / tdef.get_bitrate())

    if not os.access(options.directory, os.F_OK):
            os.makedirs(options.directory)

    dscfg = DownloadStartupConfig()
    dscfg.set_dest_dir(options.directory)
    global my_dir
    my_dir = options.directory
    dscfg.set_video_events([simpledefs.VODEVENT_START,
                            simpledefs.VODEVENT_PAUSE,
                            simpledefs.VODEVENT_RESUME])
    dscfg.set_video_event_callback(vod_event_callback)
    dscfg.set_max_speed(simpledefs.DOWNLOAD, options.dlrate)
    dscfg.set_max_speed(simpledefs.UPLOAD, options.ulrate)

    if dscfg.get_mode() == simpledefs.DLMODE_VOD:
        print >>sys.stderr, 'Client runs in streaming mode'
    
    d = s.start_download(tdef, dscfg)
    
    d.set_state_callback(state_event_callback)

    time.sleep(1)

    communicator = TrackerCommunicator(tracker_url, options.port, d.sd.peerid)
    #communicator.send_registration()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        exit_handler()