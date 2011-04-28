import logging
import os
import pickle
import time
import urllib

from binascii import b2a_hex
from traceback import print_exc
from BaseLib.Core import simpledefs

from SisClient.Cache.IoP_WSClientImpl import IoP_WSClientImpl
from SisClient.Common.PeerCallbackInterface import PeerCallbackInterface
from SisClient.Utils import serialize
from SisClient.Utils.common_utils import get_id

class PeerReporter(PeerCallbackInterface):
    def __init__(self, name):
        self._logger = logging.getLogger("Status."+name)
        self.prev_status=None
        
    def state_callback(self, ds):
        try:
            d = ds.get_download()
            p = "%.0f %%" % (100.0 * ds.get_progress())
            dl = "dl %.0f" % (ds.get_current_speed(simpledefs.DOWNLOAD))
            ul = "ul %.0f" % (ds.get_current_speed(simpledefs.UPLOAD))
            peers = "n %0d" % (ds.get_num_peers())
            
            torrentFile = d.get_def().get_name_as_unicode()
            status = ds.get_status()
            logstr = simpledefs.dlstatus_strings[status], p, dl, ul, peers, " torrent: %s" % torrentFile
            self._logger.info(logstr)
            self.prev_status = status
        except:
            print_exc()
            
        return (1.0, False)
    
    def video_event_callback(self, d, event, params):
        pass

#___________________________________________________________________________________________________

class PeerHTTPReporter(PeerCallbackInterface):
    '''
    Reporter for the SmoothIT monitoring interface.
    '''
    def __init__(self, name, id, serverAddress, scfg, compress=False, ser_method='xml', is_iop=False, report_interval=5.0):
        self._logger = logging.getLogger("Status.%s" % id)
        self.serverAddress = serverAddress
        self.report_interval = report_interval 
        self.last_report_ts = dict()
        self.do_reporting = True
        self.scfg = scfg
        self.id = id
        self.is_iop = is_iop
        self.compress_xml_reports = compress
        if self.serverAddress and not self.serverAddress=="":
            self._logger.warn("Enable reporting to "+self.serverAddress)
            if self.compress_xml_reports:
                self._logger.warn("Enable report compression")
        self.method = ser_method
        
    def _dispatch_data_to_server(self, report):
        # report at regular intervals
        now = time.time()
        filename = report['filename']
        if not self.last_report_ts.has_key(filename):
            self.last_report_ts[filename] = 0
            
        if now - self.last_report_ts[filename] < self.report_interval:
            return
        self.last_report_ts[filename] = now
        
        if self.serverAddress in ["", None]:
            self._logger.info("No monitor server specified, skip reporting")
            return
        
        # serialize the report dict
        dispatch = None
        self._logger.info(self.method)
        if (self.method == "xml"):
            dispatch = serialize.serialize(report, 
                                           compress=self.compress_xml_reports,
                                           encodeBase64=True)
        else :
            dispatch = pickle.dumps(report)
        
        try: 
            self._logger.info("send report to "+self.serverAddress)
            sock = urllib.urlopen(self.serverAddress, dispatch, proxies={})
            result = sock.read()
            sock.close()
        except:
            self._logger.error("Failed to send report to %s" % self.serverAddress, exc_info=True)
            #self._logger.info("Report was %s" % report)
        
    def state_callback(self, ds):
        
        if ds.get_status()<simpledefs.DLSTATUS_DOWNLOADING:
            self._logger.info("Don't send reports in pre-download state!")
            return
        
        chokestr = lambda b: ["c","C"][int(bool(b))]
        intereststr = lambda b: ["i","I"][int(bool(b))]
        optstr = lambda b: ["o","O"][int(bool(b))]
        protstr = lambda b: ["bt","g2g"][int(bool(b))]
        
        now = time.time()
        v = ds.get_vod_stats() or { "played": 0, "stall": 0, "late": 0, "dropped": 0, "prebuf": -1, "pieces": {} }
        # TODO (mgu): get_videoinfo() is no longer a method provided by the DownloadStatus object
        # do we need this information anyways?
        # OLD: vi = ds.get_videoinfo() or { "live": False, "inpath": "(none)", "status": None }
        vi = { "live": False, "inpath": "(none)", "status": None }
        
        vs = vi["status"]           
        
        scfg = self.scfg
        
        down_total, down_rate, up_total, up_rate = 0.0, 0.0, 0.0, 0.0
        peerinfo = {}
        valid_range=""
        if not ds.get_peerlist() is None:
            for p in ds.get_peerlist():
                down_total += p["dtotal"]/1024.0
                down_rate  += p["downrate"]/1024.0
                up_total   += p["utotal"]/1024.0
                up_rate    += p["uprate"]/1024.0

                id = p["id"]
                peerinfo[id] = {
                                "g2g": protstr(p["g2g"]),
                                "addr": "%s:%s:%s" % (p["ip"],p["port"],p["direction"]),
                                "id": id,
                                "g2g_score": "%s,%s" % (p["g2g_score"][0],p["g2g_score"][1]),
                                "down_str": "%s%s" % (chokestr(p["dchoked"]),intereststr(p["dinterested"])),
                                "down_total": p["dtotal"]/1024.0,
                                "down_rate": p["downrate"]/1024.0,
                                "up_str": "%s%s%s" % (chokestr(p["uchoked"]),intereststr(p["uinterested"]),optstr(p["optimistic"])),
                                "up_total": p["utotal"]/1024.0,
                                "up_rate": p["uprate"]/1024.0,
                                }

                if vs:
                    valid_range = vs.download_range()
                else:
                    valid_range = ""
        d = ds.get_download()
        try:
            bt1dl = d.sd.get_bt1download()
            (up_total, down_total) = bt1dl.get_transfer_stats()
            down_total = down_total/1024
            up_total = up_total/1024
        except:
            pass
        
        peerid = "UNKNOWN"
        try:
            peerid = ds.get_download().sd.peerid
        except:
            pass

        report = {
            "timestamp":  int(time.time()*1000),
            "id"        : self.id,
            "iop_flag"    : int(self.is_iop),
            "status"    : `ds.get_status()`,
            "listenport": scfg.get_listen_port(),
            "infohash":     b2a_hex(ds.get_download().get_def().get_infohash()),
            "filename":    str(d.get_def().get_name_as_unicode()),
            "peerid":     peerid,
            "live":       vi["live"],
            "progress":   100.00*ds.get_progress(),
            "down_total": down_total,
            #"down_rate":  down_rate,
            "down_rate":  ds.get_current_speed(simpledefs.DOWNLOAD),
            "up_total":   up_total,
            #"up_rate":    up_rate,
            "up_rate":    ds.get_current_speed(simpledefs.UPLOAD),
            "p_played":   v['played'],
            "t_stall":    int(v["stall"]),
            "p_late":     v["late"],
            "p_dropped":  v["dropped"],
            "t_prebuf":   int(v["prebuf"]),
            "peers":      peerinfo.values(),
            "pieces":     v["pieces"],
            "validrange": str(valid_range),
            "blockstats": ds.get_block_stats()
        }
        
        #FIXME: add to report!
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("New block_stats %s" % ds.get_block_stats())
        
        self._dispatch_data_to_server(report)
        
    def video_event_callback(self, d, event, params):
        pass

#___________________________________________________________________________________________________

class PeerLocalReporter(PeerCallbackInterface):
    def __init__(self, name, id, session, basedir):
        self.name = name
        self.id = id
        self.session = session
        self.basedir = basedir
        self.files = dict()
        self.peers = dict()
        self.stats = None
    
    def state_callback(self, ds):    
        d = ds.get_download()
            
        filename = str(d.get_def().get_name_as_unicode())
        if not self.files.has_key(filename):
            path = os.path.join(self.basedir, "%s_%s.dat" % (filename, self.name))
            handler = open(path, "w")
            self.files[filename] = {
                                     "clientname": self.name,
                                     "peer_id": ds.get_peerid(),
                                     "up_total": 0,
                                     "down_total": 0,
                                     "leeching_start": None, 
                                     "leeching_finished": None,
                                     "seeding_start": None, 
                                     "seeding_finished": None,
                                     "complete": 0,
                                     "handler": handler,
                                     "peer_info": dict()
                                     }
        
        now = time()
        if not ds.get_peerlist() is None:
            for p in ds.get_peerlist():
                id = p["id"]
                self.files[filename]['peer_info'][id] =  {
                                                          'ip':         p['ip'],
                                                          'id':         p['id'],
                                                          'down_total': p['dtotal']/1024.0,
                                                          'up_total':   p['utotal']/1024.0
                                                          }
               
        bt1dl = d.sd.get_bt1download()
        try:
            (up_total, down_total) = bt1dl.get_transfer_stats()
            down_total = down_total/1024
            up_total = up_total/1024
        except:
            down_total = 0
            up_total = 0
        
        report = {
            "timestamp":  int(time.time()*1000),
            "id"        : self.id,
            "status"    : `ds.get_status()`,
            "listenport": self.session.get_listen_port(),
            "infohash":   `ds.get_download().get_def().get_infohash()`,
            "filename":    filename,
            "peerid":     `ds.get_peerid()`,
            "progress":   100.00*ds.get_progress(),
            "down_total": down_total,
            "down_rate":  ds.get_current_speed(simpledefs.DOWNLOAD),
            "up_total":   up_total,
            "up_rate":    ds.get_current_speed(simpledefs.UPLOAD),
        }
        try:
            self.add_report(report)
        except:
            pass
         
    def add_report(self, report):
        filename = report['filename']
        file = self.files[filename]
        self.set_timemarks(report, file)            
        file['handler'].write('%f %f %f\n' % (report['timestamp'], report['down_rate'], report['up_rate']))
        file['handler'].flush()
        file['up_total'] = report['up_total']
        file['down_total'] = report['down_total']
        file['complete'] = report['progress']
        
    def set_timemarks(self, report, file):
        if file['leeching_start'] == None and int(report['status']) == simpledefs.DLSTATUS_DOWNLOADING:
            file['leeching_start'] = report['timestamp']
        if file['seeding_start'] == None and int(report['status']) == simpledefs.DLSTATUS_SEEDING:
            file['seeding_start'] = report['timestamp']
        if int(report['status']) == simpledefs.DLSTATUS_DOWNLOADING:
            file['leeching_finished'] = report['timestamp']
        if int(report['status']) == simpledefs.DLSTATUS_SEEDING:
            file['seeding_finished'] = report['timestamp']
    
    def write_stats(self):
        path = os.path.join(self.basedir, "%s_stats.txt" % self.name)
        handler = open(path, "w")

        for (filename, stats) in self.files.items(): 
            try:
                dl_time = stats['leeching_finished'] - stats['leeching_start']
            except:
                dl_time = 0
                
            try:
                seeding_time = stats['seeding_finished'] - stats['seeding_start']
            except:
                seeding_time = 0
            
            handler.write("clientname=%s\n" % stats['clientname'])
            handler.write("peer_id=%s\n" % stats['peer_id'])
            handler.write("filename=%s\n" % filename)
            handler.write("IP=%s\n" % self.session.get_external_ip())
            handler.write("Port=%s\n" % self.session.get_listen_port())
            handler.write("up_total=%f\n" % stats['up_total'])
            handler.write("down_total=%f\n" % stats['down_total'])
            handler.write("leeching_start=%s\n" % str(stats['leeching_start']))
            handler.write("leeching_finished=%s\n" % str(stats['leeching_finished']))
            handler.write("seeding_start=%s\n" % str(stats['seeding_start']))
            handler.write("seeding_finished=%s\n" % str(stats['seeding_finished']))
            handler.write("dl_time=%f\n" % dl_time)
            handler.write("seeding_time=%f\n" % seeding_time)
            handler.write("complete=%s\n" % stats['complete'])
            
            handler.write("peer info:\n")

            for peer in stats['peer_info'].values():
                handler.write("%s %s %f %f\n" % (peer['ip'], peer['id'], peer['down_total'], peer['up_total']))
            
            stats['handler'].close()
            
        handler.close()
        
    def video_event_callback(self, d, event, params):
        pass
    
#___________________________________________________________________________________________________

class PeerActivityReportEmitter(PeerCallbackInterface):
    def __init__(self, own_addr, emit_interval, sis_iop_endpoint_url="http://localhost:8080/sis/IoPEndpoint"):
        self._emit_interval = emit_interval # in seconds
        self._ws = IoP_WSClientImpl(sis_iop_endpoint_url)
        self._last_timestamp = time.time()
        self._own_address = own_addr
        self._logger = logging.getLogger("Status.%s" % self.__class__.__name__)
    
    def state_callback(self, ds):
        self._logger.debug("state_callback called")
        ts = time.time()
        #self._logger.info("ts is %s" % str(ts))
        # check if we have to file an activity report right now
        # if not, just return
        if not ts - self._last_timestamp >= self._emit_interval:
            return
        
        try:
            d = ds.get_download()
            self._logger.info("torrent: %s" % ds.get_download().get_def().get_name_as_unicode())
            torrent_id = get_id(d.get_def())
            torrent_url = "unknown"
            torrent_progress = int(ds.get_progress()*100)
            torrent_size = d.get_def().get_length()
            downloads = [ ( torrent_id, torrent_url, torrent_size, torrent_progress ) ]
        
            self._ws.report_activity(self._own_address[0], self._own_address[1], downloads)
            self._last_timestamp = ts
        except:
            self._logger.error("an error occured: could not retrieve torrent stats from resp. download object")
    
    def video_event_callback(self, d, event, params):
        # not implemented
        pass