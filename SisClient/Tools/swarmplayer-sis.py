# Written by Arno Bakker, Choopan RATTANAPOKA, Jie Yang
# see LICENSE.txt for license information
# Updated by Sebastian Schmidt, Konstantin Pussep (TUD) to support SmoothIT-specific parameters
#
# TODO: set 'download_slice_size' to 32K, such that pieces are no longer
# downloaded in 2 chunks. This particularly avoids a bad case where you
# kick the source: you download chunk 1 of piece X
# from lagging peer and download chunk 2 of piece X from source. With the piece
# now complete you check the sig. As the first part of the piece is old, this
# fails and we kick the peer that gave us the completing chunk, which is the 
# source.
#
# Note that the BT spec says: 
# "All current implementations use 2 15 , and close connections which request 
# an amount greater than 2 17." http://www.bittorrent.org/beps/bep_0003.html
#
# So it should be 32KB already. However, the BitTorrent (3.4.1, 5.0.9), 
# BitTornado and Azureus all use 2 ** 14 = 16KB chunks.
from SisClient.Common import constants

import os
import sys

try:
    if sys.frozen == "windows_exe":
        # this will avoid creation of default log file and annoying message box
        sys.stderr = open("swarmplayer.log", "w")
except:
    pass

import time
import commands
import tempfile
import urllib2
import urllib
import random
import logging
import logging.config
from SisClient.PeerSelection import BiasedUnchoking
from SisClient.PeerSelection import NeighborSelection
from SisClient.RankingPolicy import RankingPolicy
from SisClient.Client.ClientConfiguration import ClientConfiguration
from SisClient.Utils import common_utils #, net_utils

from SisClient.Common.PeerCallbackHandlers import PeerCallbackHandlers
from SisClient.Common.CommonPeerHandlers import PeerHTTPReporter,\
    PeerActivityReportEmitter
from SisClient.Client.ClientCallbackHandlers import VoDClientHighRangeStatusHandler,\
    ClientHAPHandler

from SisClient.Tools.vodclient import TrackerCommunicator

from threading import enumerate, currentThread, RLock
from traceback import print_exc

if sys.platform == "darwin":
    # on Mac, we can only load VLC/OpenSSL libraries
    # relative to the location of tribler.py
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
try:
    import wxversion
    wxversion.select('2.8')
except:
    pass

import wx

from BaseLib.__init__ import LIBRARYNAME
from BaseLib.Core.API import *
from BaseLib.Core.Utilities.unicode import bin2unicode
from BaseLib.Policies.RateManager import UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager

from BaseLib.Video.defs import * 
from BaseLib.Video.VideoPlayer import VideoPlayer, VideoChooser  
from BaseLib.Player.PlayerVideoFrame import VideoFrame

from BaseLib.Player.systray import PlayerTaskBarIcon
from BaseLib.Player.Reporter import Reporter
from BaseLib.Utilities.Instance2Instance import *

from BaseLib.Player.UtilityStub import UtilityStub
from BaseLib.Video.utils import videoextdefaults

import optparse
#from ConfigParser import *

# TEMPVLCRAW
from threading import Timer

DEBUG = False
ONSCREENDEBUG = False
ALLOW_MULTIPLE = False
RATELIMITADSL = False

DISKSPACE_LIMIT = 5L * 1024L * 1024L * 1024L  # 5 GB
DEFAULT_MAX_UPLOAD_SEED_WHEN_SEEDING = 75 # KB/s
I2I_LISTENPORT = 57894
PLAYER_LISTENPORT = 8620
VIDEOHTTP_LISTENPORT = 6879

class PlayerFrame(VideoFrame):
    def __init__(self, parent):
        VideoFrame.__init__(self,parent,parent.utility,parent.appname,parent.iconpath,parent.videoplayer.get_vlcwrap(),parent.logopath)        
        self.parent = parent
        self.closed = False
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    def OnCloseWindow(self, event=None):
        
        print >> sys.stderr, "main: ON CLOSE WINDOW"

        # TODO: first event.Skip does not close window, second apparently does
        # Check how event differs

        if event is not None:
            nr = event.GetEventType()
            lookup = { wx.EVT_CLOSE.evtType[0]: "EVT_CLOSE", wx.EVT_QUERY_END_SESSION.evtType[0]: "EVT_QUERY_END_SESSION", wx.EVT_END_SESSION.evtType[0]: "EVT_END_SESSION" }
            if nr in lookup: 
                nr = lookup[nr]
            print >> sys.stderr, "main: Closing due to event ", nr
            event.Skip()
        else:
            print >> sys.stderr, "main: Closing untriggered by event"

        # This gets called multiple times somehow
        if not self.closed:
            self.closed = True
            self.parent.videoFrame = None

            self.parent.videoplayer.stop_playback()
            self.parent.remove_current_download_if_not_complete()
            # self.parent.restart_other_downloads()
            
        print >> sys.stderr, "main: Closing done"
        # TODO: Show balloon in systray when closing window to indicate things continue there



class PlayerApp(wx.App,InstanceConnectionHandler):
    def __init__(self, x, params, single_instance_checker, installdir, config, sc):
        self.params = params
        self.single_instance_checker = single_instance_checker
        self.installdir = installdir
        self.error = None
        self.s = None
        self.tbicon = None
        
        # TODO: Arno: we can get rid of dlock now stats processing is delegated to GUI thread:
        # Verify all places where it is used e.g. in sesscb_remove_current_callback()
        # another thread than Main uses it.  
        self.dlock = RLock()  
        self.d = None # protected by dlock
        self.playermode = DLSTATUS_DOWNLOADING # protected by dlock
        self.r = None # protected by dlock
        self.count = 0
        self.said_start_playback = False
        self.decodeprogress = 0
        self.shuttingdown = False
        self.getpeerlistcount = 2
        self.decodeprogress = 0
        self.config = config
        self.appname = "SmoothIT Player"
        self.sc = sc # SmoothIT related configuration
        self._handlers = PeerCallbackHandlers("SmoothIT Player", 1.0)
        self.supporter_handler = VoDClientHighRangeStatusHandler()
        if sc.is_hap_enabled():
            logger.info("HAP support enabled")
            self._handlers.register_handler(ClientHAPHandler(sc))
            
        self._supporter_callback_registered = False
        
        
        InstanceConnectionHandler.__init__(self,self.i2icallback)
        wx.App.__init__(self, x)
        
    def OnInit(self):
        try:
            has_torrent =  ('torrent' in self.config and self.config['torrent'] is not None)
            # Load torrent
            if has_torrent:                
                torrentfilename = self.config['torrent']
                print >> sys.stderr, "TORRENT FILE IS ", torrentfilename                
                        
            # If already running, and user starts a new instance without a URL 
            # on the cmd line
            if self.single_instance_checker.IsAnotherRunning():
                print >> sys.stderr, "main: Another instance running..."                   
                if has_torrent:                
                    i2ic = Instance2InstanceClient(I2I_LISTENPORT, 'START', torrentfilename)
                return False
            
            # Normal startup
            # Read config
            state_dir = Session.get_default_state_dir(self.config['base_dir'])
            dldir = self.config['dl_dir']            
            
            self.utility = UtilityStub(self.installdir, state_dir)
            self.utility.app = self
            print >> sys.stderr, self.utility.lang.get('build')
            self.iconpath = os.path.join(self.installdir, LIBRARYNAME, 'Images', 'SwarmPlayerIcon.ico')
            self.logopath = os.path.join(self.installdir, LIBRARYNAME, 'Images', 'SwarmPlayerLogo.png')

            
            # Start server for instance2instance communication
            # self.i2is = Instance2InstanceServer(I2I_LISTENPORT, self.i2icallback) 
            self.i2is = Instance2InstanceServer(I2I_LISTENPORT,self,timeout=(24.0*3600.0)) 
            self.i2is.start()

            self.videoplayer = None
            self.videoFrame = None
            if has_torrent:
                self.create_video_player()
                self.start_video_frame()

            # The playerconfig contains all config parameters that are not
            # saved by checkpointing the Session or its Downloads.
            self.load_playerconfig(state_dir)

            # Install systray icon
            # Note: setting this makes the program not exit when the videoFrame
            # is being closed.
            
            self.tbicon = PlayerTaskBarIcon(self, self.iconpath)
            
            # Start Tribler Session
            cfgfilename = Session.get_default_config_filename(state_dir)
            
            if DEBUG:
                print >> sys.stderr, "main: Session config", cfgfilename
            try:
                self.sconfig = SessionStartupConfig.load(cfgfilename)
            except:
                #print_exc()
                self.sconfig = SessionStartupConfig()
                self.sconfig.set_state_dir(state_dir)
                
                self.sconfig.set_listen_port(PLAYER_LISTENPORT)    
                self.sconfig.set_overlay(False)
                self.sconfig.set_megacache(False)

            self.s = Session(self.sconfig)
            self.s.set_supporter_ips(self.config['supporter_ips'])
            self.s.set_download_states_callback(self.sesscb_states_callback)

            self.reporter = Reporter(self.sconfig)
            #SmoothIT_: we need Session to exist so we can obtain the external ip
            
            self._handlers.register_handler(self.supporter_handler)
            self._handlers.register_handler(PeerHTTPReporter("SmoothIT Player",
                                            self.sc.get_id(),
                                            self.sc.get_report_to(),
                                            self.sconfig,
                                            self.sc.get_compress_xml_reports(),
                                            self.sc.get_serialization_method(),
                                            report_interval=self.sc.get_report_interval()))

            if self.sc.get_sis_url() != None:
                ip_addr = self.s.get_external_ip()
                self._handlers.register_handler(PeerActivityReportEmitter(
                    (ip_addr, self.sc.get_port()),
                    self.sc.get_activity_report_interval(),
                    sis_iop_endpoint_url=self.sc.get_sis_iop_url()))
                logger.info("Activity reports for IoP enabled.")
            #_SmoothIT

            if RATELIMITADSL:
                self.r = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
                self.r.set_global_max_speed(DOWNLOAD, 400)
                self.r.set_global_max_speed(UPLOAD, 90)            
            # Arno: For extra robustness, ignore any errors related to restarting
            try:
                # Load all other downloads in cache, but in STOPPED state
                self.s.load_checkpoint(initialdlstatus=DLSTATUS_SEEDING)
            except:
                print_exc()

            # This is only for old downloads, new ones will be registered separately
            for download in self.s.get_downloads():
                download.set_state_callback(self._handlers.state_callback, getpeerlist=True)
                            
            # Load torrent
            if has_torrent:                
                # Start download                
                if not self.start_download(torrentfilename, dldir):
                    self.OnExit()
                    return False
                                        
            if not has_torrent:
                wx.MessageDialog(None, "The player was launched in background and will be seeding files you have previously downloaded to other clients.\nPlease try to keep it running at all times to help others!", "SmoothIT Client", wx.OK|wx.ICON_INFORMATION).ShowModal()
            
        except Exception, e:
            print_exc()
            self.show_error(str(e))
            self.OnExit()
            return False
        return True

    def create_video_player(self):
        # Fire up the VideoPlayer, it abstracts away whether we're using
        # an internal or external video player.
        self.videoplayer = VideoPlayer.getInstance(httpport=VIDEOHTTP_LISTENPORT)
        playbackmode = PLAYBACKMODE_INTERNAL
        self.videoplayer.register(self.utility, preferredplaybackmode=playbackmode)

    def start_video_frame(self):
        # Start video frame
        self.videoFrame = PlayerFrame(self)
        self.Bind(wx.EVT_CLOSE, self.videoFrame.OnCloseWindow)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.videoFrame.OnCloseWindow)
        self.Bind(wx.EVT_END_SESSION, self.videoFrame.OnCloseWindow)
        self.videoFrame.show_videoframe()

        if self.videoplayer is not None:
            self.videoplayer.set_videoframe(self.videoFrame)
        self.said_start_playback = False
        
    def select_torrent_from_disk(self):
        dlg = wx.FileDialog(None,
                            'SwarmPlayer: Select torrent to play',
                            '', # default dir
                            '', # default file
                            'TSTREAM and TORRENT files (*.tstream;*.torrent)|*.tstream;*.torrent',
                            wx.OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        else:
            filename = None
        dlg.Destroy()
        return filename

    def ask_user_to_select_video(self, videofiles):
        dlg = VideoChooser(self.videoFrame, self.utility, videofiles, title='SwarmPlayer', expl='Select which file to play')
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            index = dlg.getChosenIndex()
            filename = videofiles[index]
        else:
            filename = None
        dlg.Destroy()
        return filename


    def start_download(self, torrentfilename, download_directory=None):
        
        tdef = TorrentDef.load(torrentfilename)
        print >> sys.stderr, "main: Starting download, infohash is", `tdef.get_infohash()`
        
        # Select which video to play (if multiple)
        videofiles = tdef.get_files(exts=videoextdefaults)
        print >> sys.stderr, "main: Found video files", videofiles
        
        if len(videofiles) == 0:
            print >> sys.stderr, "main: No video files found! Let user select"
            # Let user choose any file
            videofiles = tdef.get_files(exts=None)
            
        if len(videofiles) > 1:
            selectedvideofile = self.ask_user_to_select_video(videofiles)
            if selectedvideofile is None:
                print >> sys.stderr, "main: User selected no video"
                return False
            dlfile = selectedvideofile
        else:
            dlfile = videofiles[0]
        
        # Free diskspace, if needed
        destdir = download_directory or self.get_default_destdir()
        if not os.access(destdir, os.F_OK):
            os.mkdir(destdir)

        # Arno: For extra robustness, ignore any errors related to restarting
        # TODO: Extend code such that we can also delete files from the 
        # disk cache, not just Downloads. This would allow us to keep the
        # parts of a Download that we already have, but that is being aborted
        # by the user by closing the video window. See remove_current_*
        try:
            if not self.free_up_diskspace_by_downloads(tdef.get_infohash(), tdef.get_length([dlfile])):
                print >> sys.stderr, "main: Not enough free diskspace, ignoring"
                #return False
                pass # Let it slide
        except:
            print_exc()
        
        # Setup how to download
        dcfg = DownloadStartupConfig()
        
        # Delegate processing to VideoPlayer
        dcfg.set_video_event_callback(self.videoplayer.sesscb_vod_event_callback)
        dcfg.set_video_events(self.videoplayer.get_supported_vod_events())

        dcfg.set_dest_dir(destdir)
        
        if tdef.is_multifile_torrent():
            dcfg.set_selected_files([dlfile])
        
        # Arno: 2008-7-15: commented out, just stick with old ABC-tuned 
        # settings for now
        #dcfg.set_max_conns_to_initiate(300)
        #dcfg.set_max_conns(300)
        con_lim = self.sc.get_connection_limit()
        dcfg.set_max_conns(con_lim)
        dcfg.set_max_conns_to_initiate((con_lim+1)/2)
        dcfg.set_min_peers((con_lim+2)/3)
        dcfg.set_max_uploads(self.sc.get_max_upload_slots_per_download())
        
        # Start download
        dlist = self.s.get_downloads()
        infohash = tdef.get_infohash()

        # Start video window if not open
        if self.videoFrame is None:
            self.start_video_frame()
        else:
            # Stop playing, reset stream progress info + sliders 
            self.videoplayer.stop_playback(reset=True)
            self.said_start_playback = False
        self.decodeprogress = 0
        
        # Stop all
        newd = None
        for d in dlist:
            if d.get_def().get_infohash() == infohash:
                # Download already exists.
                # One safe option is to remove it (but not its downloaded content)
                # so we can start with a fresh DownloadStartupConfig. However,
                # this gives funky concurrency errors and could prevent a
                # Download from starting without hashchecking (as its checkpoint
                # was removed) 
                # Alternative is to set VOD callback, etc. at Runtime:
                print >> sys.stderr, "main: Reusing old duplicate Download", `infohash`
                newd = d
                d.stop()

        self.s.lm.h4xor_reset_init_conn_counter()

        self.dlock.acquire()
        try:
            self.playermode = DLSTATUS_DOWNLOADING
            if newd is None:
                print >> sys.stderr, "main: Starting new Download", `infohash`
                newd = self.s.start_download(tdef, dcfg)                
                newd.set_state_callback(self._handlers.state_callback, getpeerlist=True)
            else:
                # Delegate processing to VideoPlayer
                newd.set_video_event_callback(self.videoplayer.sesscb_vod_event_callback)
                newd.set_video_events(self.videoplayer.get_supported_vod_events())

                if tdef.is_multifile_torrent():
                    newd.set_selected_files([dlfile])
                print >> sys.stderr, "main: Restarting existing Download", `infohash`
                newd.restart()
                # seems that we need it here too
                newd.set_state_callback(self._handlers.state_callback, getpeerlist=True)

            self.d = newd
            
            #SmoothIT_: supporter callback and download limitation
            # register supporter callback for every swarm
            self._register_supporter_callback(newd)
            
            
            # self.d.set_max_speed(DOWNLOAD, self.config['rates'][1])
            self.d.sd.set_max_speed(DOWNLOAD,self.config['rates'][1],None)
            #KP: could do the same for UPLOAD if needed
            #_SmoothIT
        finally:
            self.dlock.release()

        print >> sys.stderr, "main: Saving content to", self.d.get_dest_files()

        cname = tdef.get_name_as_unicode()
        if len(videofiles) > 1:
            cname += u' - ' + bin2unicode(dlfile)
        self.videoplayer.set_content_name(u'Loading: ' + cname)
        
        try:
            [mime, imgdata] = tdef.get_thumbnail()
            if mime is not None:
                f = StringIO(imgdata)
                img = wx.EmptyImage(- 1, - 1)
                img.LoadMimeStream(f, mime, - 1)
                self.videoplayer.set_content_image(img)
            else:
                self.videoplayer.set_content_image(None)
        except:
            print_exc()

        return True
    
    def _register_supporter_callback(self, download):
        '''
        SmoothIT: aks supporter for help if cannot fill the buffer.
        '''
        tracker_url = download.get_def().get_tracker()[:download.get_def().get_tracker().find("announce")]
        time.sleep(1)
        comm = TrackerCommunicator(tracker_url, self.sc.get_port(), download.sd.peerid)
        self.supporter_handler.set_communicator(comm)
        
        #also for the alternative implementation
        print >> sys.stderr, "main: got ips %s " % self.config['supporter_ips']
                
        
    def _unregister_supporter_callback(self):
        if self.supporter_handler is not None:
            self.supporter_handler.set_communicator(None)

    def i2icallback(self, ic, cmd):
        """ Called by Instance2Instance thread """
        
        print >> sys.stderr, "main: Another instance called us with cmd", cmd
        
        if cmd.startswith('START '):
            param = cmd[len('START '):]
            torrentfilename = None
            if param.startswith('http:'):
                # Retrieve from web 
                f = tempfile.NamedTemporaryFile()
                n = urlOpenTimeout(param)
                data = n.read()
                f.write(data)
                f.close()
                n.close()
                torrentfilename = f.name
            else:
                torrentfilename = param
                
            # Switch to GUI thread
            wx.CallAfter(self.remote_start_download, torrentfilename)

    def remote_start_download(self, torrentfilename):
        if not self.videoplayer:
            self.create_video_player()
            
        if not self.videoFrame:
            self.start_video_frame()            
        
        """ Called by GUI thread """
        self.videoplayer.stop_playback(reset=True)

        self.remove_current_download_if_not_complete()
        self.start_download(torrentfilename)

    def videoserver_error_callback(self, e, url):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videoserver_error_guicallback, e, url)
        
    def videoserver_error_guicallback(self, e, url):
        print >> sys.stderr, "main: Video server reported error", str(e)
        #    self.show_error(str(e))
        pass

    def videoserver_set_status_callback(self, status):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videoserver_set_status_guicallback, status)

    def videoserver_set_status_guicallback(self, status):
        if self.videoFrame is not None:
            self.videoFrame.set_player_status(status)
    
    def free_up_diskspace_by_downloads(self, infohash, needed):
        
        if DEBUG:
            print >> sys.stderr, "main: free_up: needed", needed, DISKSPACE_LIMIT
        if needed > DISKSPACE_LIMIT:
            # Not cleaning out whole cache for bigguns
            if DEBUG:
                print >> sys.stderr, "main: free_up: No cleanup for bigguns"
            return True 
        
        inuse = 0L
        timelist = []
        dlist = self.s.get_downloads()
        for d in dlist:
            hisinfohash = d.get_def().get_infohash()
            if infohash == hisinfohash:
                # Don't delete the torrent we want to play
                continue
            destfiles = d.get_dest_files()
            if DEBUG:
                print >> sys.stderr, "main: free_up: Downloaded content", `destfiles`
            
            dinuse = 0L
            for (filename, savepath) in destfiles:
                stat = os.stat(savepath)
                dinuse += stat.st_size
            inuse += dinuse
            timerec = (stat.st_ctime, dinuse, d)
            timelist.append(timerec)
            
        if inuse + needed < DISKSPACE_LIMIT:
            # Enough available, done.
            if DEBUG:
                print >> sys.stderr, "main: free_up: Enough avail", inuse
            return True
        
        # Policy: remove oldest till sufficient
        timelist.sort()
        if DEBUG:
            print >> sys.stderr, "main: free_up: Found", timelist, "in dest dir"
        
        got = 0L
        for ctime, dinuse, d in timelist:
            print >> sys.stderr, "main: free_up: Removing", `d.get_def().get_name_as_unicode()`, "to free up diskspace, t", ctime
            self.s.remove_download(d, removecontent=True)
            got += dinuse
            if got > needed:
                return True
        # Deleted all, still no space:
        return False
        
        
    def show_error(self, msg):
        dlg = wx.MessageDialog(None, msg, "SwarmPlayer Error", wx.OK | wx.ICON_ERROR)
        result = dlg.ShowModal()
        dlg.Destroy()
        
    def OnExit(self):
        print >> sys.stderr, "main: ONEXIT"
        self.shuttingdown = True
        self.remove_current_download_if_not_complete()

        # To let Threads in Session finish their business before we shut it down.
        time.sleep(2) 
        
        if self.s is not None:
            self.s.shutdown()
        
        if self.tbicon is not None:
            self.tbicon.RemoveIcon()
            self.tbicon.Destroy()

        ts = enumerate()
        for t in ts:
            print >> sys.stderr, "main: ONEXIT: Thread still running", t.getName(), "daemon", t.isDaemon()
        
        if not ALLOW_MULTIPLE:
            del self.single_instance_checker
        self.ExitMainLoop()

    def sesscb_states_callback(self, dslist):
        """ Called by Session thread """
        # Arno: delegate to GUI thread. This makes some things (especially
        #access control to self.videoFrame easier
        #self.gui_states_callback(dslist)
        
        # Arno: we want the prebuf stats every second, and we want the
        # detailed peerlist, needed for research stats. Getting them every
        # second may be too expensive, so get them every 10.
        #
        self.getpeerlistcount += 1
        getpeerlist = (self.getpeerlistcount % 10) == 0
        haspeerlist = (self.getpeerlistcount % 10) == 1
        
        wx.CallAfter(self.gui_states_callback, dslist, haspeerlist)
        
        #print >>sys.stderr,"main: SessStats:",self.getpeerlistcount,getpeerlist,haspeerlist
        return (1.0, getpeerlist) 

    def gui_states_callback(self, dslist, haspeerlist):
        """ Called by *GUI* thread.
        CAUTION: As this method is called by the GUI thread don't to any 
        time-consuming stuff here! """
        
        #print >>sys.stderr,"main: Stats:"
        if self.shuttingdown:
            return
        
        # See which Download is currently playing
        self.dlock.acquire()
        playermode = self.playermode
        d = self.d
        self.dlock.release()

        totalspeed = {}
        totalspeed[UPLOAD] = 0.0
        totalspeed[DOWNLOAD] = 0.0
        totalhelping = 0

        # When not playing, display stats for all Downloads and apply rate control.
        if playermode == DLSTATUS_SEEDING:
            for ds in dslist:
                print >> sys.stderr, "main: Stats: Seeding: %s %.1f%% %s" % (dlstatus_strings[ds.get_status()], 100.0 * ds.get_progress(), ds.get_error())
            self.ratelimit_callback(dslist)
            
        # Calc total dl/ul speed and find DownloadState for current Download
        ds = None
        for ds2 in dslist:
            if ds2.get_download() == d:
                ds = ds2
            elif playermode == DLSTATUS_DOWNLOADING:
                print >> sys.stderr, "main: Stats: Waiting: %s %.1f%% %s" % (dlstatus_strings[ds2.get_status()], 100.0 * ds2.get_progress(), ds2.get_error())
            
            for dir in [UPLOAD, DOWNLOAD]:
                totalspeed[dir] += ds2.get_current_speed(dir)
            totalhelping += ds2.get_num_peers()

        # Report statistics on all downloads to research server, every 10 secs
        # SMOOTHIT (mgu): commented the underneath reporting code out since it
        # breaks with the most recent nextshare version that we use
#        if haspeerlist:
#            try:
#                for d in dslist:
#                    self.reporter.report_stat(d)
#            except:
#                print_exc()

        # Set systray icon tooltip. This has limited size on Win32!
        txt = 'SwarmPlayer\n\n'
        txt += 'DL: %.1f\n' % (totalspeed[DOWNLOAD])
        txt += 'UL:   %.1f\n' % (totalspeed[UPLOAD])
        txt += 'Helping: %d\n' % (totalhelping)
        #print >>sys.stderr,"main: ToolTip summary",txt
        self.OnSetSysTrayTooltip(txt)
        
        # No current Download        
        if ds is None:
            return
        elif playermode == DLSTATUS_DOWNLOADING:
            print >> sys.stderr, "main: Stats: DL: %s %.1f%% %s dl %.1f ul %.1f n %d\n" % (dlstatus_strings[ds.get_status()], 100.0 * ds.get_progress(), ds.get_error(), ds.get_current_speed(DOWNLOAD), ds.get_current_speed(UPLOAD), ds.get_num_peers())

        # If we're done playing we can now restart any previous downloads to 
        # seed them.
        if playermode != DLSTATUS_SEEDING and ds.get_status() == DLSTATUS_SEEDING:
            self.restart_other_downloads() # GUI UPDATE

        # cf. 25 Mbps cap to reduce CPU usage and improve playback on slow machines
        # Arno: on some torrents this causes VLC to fail to tune into the video
        # although it plays audio???
        #ds.get_download().set_max_speed(DOWNLOAD,1500) 
        #print >> sys.stderr, "****************************** speed %s ********************" % ds.get_download().get_max_speed(DOWNLOAD)


        # Don't display stats if there is no video frame to show them on.
        if self.videoFrame is None:
            return
        else:
            #self.display_stats_in_videoframe(ds, totalhelping, totalspeed)
            pass


    def display_stats_in_videoframe(self, ds, totalhelping, totalspeed):
        # Display stats for currently playing Download
        
        videoplayer_mediastate = self.videoplayer.get_state()
        #print >>sys.stderr,"main: Stats: VideoPlayer state",videoplayer_mediastate
        
        logmsgs = ds.get_log_messages()
        logmsg = None
        if len(logmsgs) > 0:
            print >> sys.stderr, "main: Log", logmsgs[0]
            logmsg = logmsgs[ - 1][1]
            
        preprogress = ds.get_vod_prebuffering_progress()
        playable = ds.get_vod_playable()
        t = ds.get_vod_playable_after()
        
        #print >>sys.stderr,"main: playble",playable,"preprog",preprogress
        #print >> sys.stderr, "main: ETA is", t, "secs"
        if t > float(2 ** 30):
            intime = "inf"
        elif t == 0.0:
            intime = "now"
        else:
            h, t = divmod(t, 60.0 * 60.0)
            m, s = divmod(t, 60.0)
            if h == 0.0:
                if m == 0.0:
                    intime = "%ds" % (s)
                else:
                    intime = "%dm:%02ds" % (m, s)
            else:
                intime = "%dh:%02dm:%02ds" % (h, m, s)
                
        #print >>sys.stderr,"main: VODStats",preprogress,playable,"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

        if ds.get_status() == DLSTATUS_HASHCHECKING:
            genprogress = ds.get_progress()
            pstr = str(int(genprogress * 100))
            msg = "Checking already downloaded parts " + pstr + "% done"
        elif ds.get_status() == DLSTATUS_STOPPED_ON_ERROR:
            msg = 'Error playing: ' + str(ds.get_error())
        elif playable:
            if not self.said_start_playback:
                msg = "Starting playback..."
                
            if videoplayer_mediastate == MEDIASTATE_STOPPED and self.said_start_playback:
                if totalhelping == 0:
                    topmsg = u"Please leave the SwarmPlayer running, this will help other SwarmPlayer users to download faster."
                else:
                    topmsg = u"Helping " + str(totalhelping) + " SwarmPlayer users to download. Please leave it running in the background."
                    
                # Display this on status line
                # TODO: Show balloon in systray when closing window to indicate things continue there
                msg = ''
                
                # Display helping info on "content name" line.
                self.videoplayer.set_content_name(topmsg)
            elif videoplayer_mediastate == MEDIASTATE_PLAYING:
                self.said_start_playback = True
                # It may take a while for VLC to actually start displaying
                # video, as it is trying to tune in to the stream (finding
                # I-Frame). Display some info to show that:
                #
                cname = ds.get_download().get_def().get_name_as_unicode()
                topmsg = u'Decoding: ' + cname + ' ' + str(self.decodeprogress) + ' s'
                self.decodeprogress += 1
                msg = ''
                # Display tuning in info on "content name" line.
                self.videoplayer.set_content_name(topmsg)
            elif videoplayer_mediastate == MEDIASTATE_PAUSED:
                msg = "Buffering... " + str(int(100.0 * preprogress)) + "%"
            else:
                msg = ''
                
        elif preprogress != 1.0:
            pstr = str(int(preprogress * 100))
            npeers = ds.get_num_peers()
            npeerstr = str(npeers)
            if npeers == 0 and logmsg is not None:
                msg = logmsg
            else:
                msg = "Prebuffering " + pstr + "% done, eta " + intime + '  (connected to ' + npeerstr + ' people)'
                
            try:
                d = ds.get_download()
                tdef = d.get_def()
                videofiles = d.get_selected_files()
                if len(videofiles) == 0:
                    videofile = None
                else:
                    videofile = videofiles[0]
                if tdef.get_bitrate(videofile) is None:
                    msg += '. This video may not play properly because its bitrate is unknown.'
            except:
                print_exc()
        else:
            msg = "Waiting for sufficient download speed... " + intime
            
        global ONSCREENDEBUG
        if msg == '' and ONSCREENDEBUG:
            uptxt = "up %.1f" % (totalspeed[UPLOAD])
            downtxt = " down %.1f" % (totalspeed[DOWNLOAD])
            peertxt = " peer %d" % (totalhelping)
            msg = uptxt + downtxt + peertxt

        # Update status msg and progress bar
        self.videoplayer.set_player_status_and_progress(msg, ds.get_pieces_complete())
        
        # Toggle save button
        self.videoplayer.set_save_button(ds.get_status() == DLSTATUS_SEEDING, self.save_video_copy)    
            
        if False: # Only works if the sesscb_states_callback() method returns (x,True)
            peerlist = ds.get_peerlist()
            print >> sys.stderr, "main: Connected to", len(peerlist), "peers"
            for peer in peerlist:
                print >> sys.stderr, "main: Connected to", peer['ip'], peer['uprate'], peer['downrate']

    def set_ratelimits(self):
        uploadrate = float(self.playerconfig['total_max_upload_rate'])
        print >> sys.stderr, "main: restart_other_downloads: Setting max upload rate to", uploadrate
        self.r.set_global_max_speed(UPLOAD, uploadrate)
        self.r.set_global_max_seedupload_speed(uploadrate)

    def ratelimit_callback(self, dslist):
        """ When the player is in seeding mode, limit the used upload to
        the limit set by the user via the options menu. 
        Called by *GUI* thread """
        if self.r is None:
            return

        # Adjust speeds once every 4 seconds
        adjustspeeds = False
        if self.count % 4 == 0:
            adjustspeeds = True
        self.count += 1
        
        if adjustspeeds:
            self.r.add_downloadstatelist(dslist)
            self.r.adjust_speeds()

    def OnSetSysTrayTooltip(self, txt):         
        if self.tbicon is not None:
            self.tbicon.set_icon_tooltip(txt)

    # vod_event_callback moved to VideoPlayer.py

    def restart_other_downloads(self):
        """ Called by GUI thread """
        if self.shuttingdown:
            return
        print >> sys.stderr, "main: Restarting other downloads"
        try:
            self.dlock.acquire()
            self.playermode = DLSTATUS_SEEDING
            self.r = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
            self.set_ratelimits()
        finally:
            self.dlock.release()

        dlist = self.s.get_downloads()
        for d in dlist:
            if d != self.d:
                d.set_mode(DLMODE_NORMAL) # checkpointed torrents always restarted in DLMODE_NORMAL, just make extra sure
                d.restart() 

    def load_playerconfig(self, state_dir):
        self.playercfgfilename = os.path.join(state_dir, 'playerconf.pickle')
        self.playerconfig = None
        try:
            f = open(self.playercfgfilename, "rb")
            self.playerconfig = pickle.load(f)
            f.close()
        except:
            #print_exc()
            logger.info("failed to load config state, ignore it")
            self.playerconfig = {}
            self.playerconfig['total_max_upload_rate'] = DEFAULT_MAX_UPLOAD_SEED_WHEN_SEEDING # KB/s

    def save_playerconfig(self):
        try:
            f = open(self.playercfgfilename, "wb")
            pickle.dump(self.playerconfig, f)
            f.close()
        except:
            print_exc()
            
    def set_playerconfig(self, key, value):
        self.playerconfig[key] = value
        
        if key == 'total_max_upload_rate':
            try:
                self.set_ratelimits()
            except:
                print_exc()
    
    def get_playerconfig(self, key):
        return self.playerconfig[key]
    
    def clear_session_state(self):
        """ Try to fix SwarmPlayer """
        try:
            self.videoplayer.stop_playback()
        except:
            print_exc()
        try:
            if self.s is not None:
                dlist = self.s.get_downloads()
                for d in dlist:
                    self.s.remove_download(d, removecontent=True)
        except:
            print_exc()
        time.sleep(1) # give network thread time to do stuff
        try:
                dldestdir = self.get_default_destdir()
                shutil.rmtree(dldestdir, True) # ignore errors
        except:
            print_exc()
        try:
                dlcheckpointsdir = os.path.join(self.s.get_state_dir(), STATEDIR_DLPSTATE_DIR)
                shutil.rmtree(dlcheckpointsdir, True) # ignore errors
        except:
            print_exc()
        try:
                cfgfilename = os.path.join(self.s.get_state_dir(), STATEDIR_SESSCONFIG)
                os.remove(cfgfilename)
        except:
            print_exc()

        self.s = None # HARD EXIT
        #self.OnExit()
        sys.exit(0) # DIE HARD 4.0
    
    def get_default_destdir(self):
        return os.path.join(self.s.get_state_dir(), 'downloads')
    
    def remove_current_download_if_not_complete(self):
        print >> sys.stderr, "main: Removing current download if not complete"
        self.dlock.acquire()
        d = self.d
        self._unregister_supporter_callback()
        if d is not None:
            d.sd.set_max_speed(DOWNLOAD,0.001,None)
        self.d = None
        self.dlock.release()
        # if d is not None:
        #     d.set_state_callback(self.sesscb_remove_current_callback)
        
    def sesscb_remove_current_callback(self, ds):
        """ Called by SessionThread """
        pass
        # d = ds.get_download()
        # if (ds.get_status() == DLSTATUS_DOWNLOADING and ds.get_progress() >= 0.9) or ds.get_status() == DLSTATUS_SEEDING:
        #     pass
        # else:
        # self.dlock.acquire()
        # try:
        #     if self.s is not None:
        #         print >> sys.stderr, "main: Removing incomplete download", `d.get_def().get_name_as_unicode()`
        #         # If you want to sleep here, to delay removal because VLC is
        #         # still playing from it, you must remove the locking.
        #         self.s.remove_download(d, removecontent=False)            
        # finally:
        #     self.dlock.release()
        # 
        #     
        # return (- 1.0, False)
        
    def save_video_copy(self):
        # Save a copy of current download to other location
        # called by gui thread
        t = Thread(target=self.save_callback)
        t.setName("SwarmplayerSave" + t.getName())
        t.setDaemon(True)
        t.start()
    
    def save_callback(self):
        # Save a copy of current download to other location
        # called by new thread from self.save_video_copy
        try:
            if sys.platform == 'win32':
                # Jelle also goes win32, find location of "My Documents"
                # see http://www.mvps.org/access/api/api0054.htm
                from win32com.shell import shell
                pidl = shell.SHGetSpecialFolderLocation(0, 0x05)
                defaultpath = shell.SHGetPathFromIDList(pidl)
            else:
                defaultpath = os.path.expandvars('$HOME')
        except Exception, msg:
            defaultpath = ''
            print_exc()
        
        self.dlock.acquire()
        dest_files = self.d.get_dest_files()
        self.dlock.release()
        
        dest_file = dest_files[0] # only single file for the moment in swarmplayer
        dest_file_only = os.path.split(dest_file[1])[1]
        print >> sys.stderr, 'Defaultpath:', defaultpath, 'Dest:', dest_file
        dlg = wx.FileDialog(self.videoFrame,
                            message=self.utility.lang.get('savemedia'),
                            defaultDir=defaultpath,
                            defaultFile=dest_file_only,
                            wildcard=self.utility.lang.get('allfileswildcard') + ' (*.*)|*.*',
                            style=wx.SAVE)
        dlg.Raise()
        result = dlg.ShowModal()
        dlg.Destroy()
        
        if result == wx.ID_OK:
            path = dlg.GetPath()
            print >> sys.stderr, 'Path:', path
            print >> sys.stderr, 'Copy: %s to %s' % (dest_file[1], path)
            if sys.platform == 'win32':
                try:
                    import win32file
                    win32file.CopyFile(dest_file[1], path, 0) # do succeed on collision
                except:
                    shutil.copyfile(dest_file[1], path)
            else:
                shutil.copyfile(dest_file[1], path)
    
class LinuxSingleInstanceChecker:
    
    def __init__(self, basename):
        self.basename = basename

    def IsAnotherRunning(self):
        "Uses pgrep to find other <self.basename>.py processes"
        # If no pgrep available, it will always start tribler
        cmd = 'pgrep -fl "%s\.py" | grep -v pgrep' % (self.basename)
        progressInfo = commands.getoutput(cmd)
        numProcesses = len(progressInfo.split('\n'))
        #if DEBUG:
        #    print 'main: ProgressInfo: %s, num: %d' % (progressInfo, numProcesses)
        return numProcesses > 1                   
        
##############################################################
#
# Main Program Start Here
#
##############################################################
def run(params=None):    
    # SmoothIT-start (edited by Sebastian Schmidt - TUD)
    arg0 = sys.argv[0].lower()
    if arg0.endswith('.exe'):
        installdir = os.path.abspath(os.path.dirname(sys.argv[0]))
    else:
        installdir = os.getcwd()
        
    # parse params
    op = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options] + torrentfile.tstream",
                     description="Run swarm player with SIS support (if the appropriate peerselection and/or neighborselection is enabled).")
        
    # Basic options
    op.add_option("-u", "--url",
                  action="store", dest="url", default=None,
                  help="URL of SIS client interface, optional")
    
    op.add_option("-b", "--ranking_source",
                  action="store", dest="ranking_source",
                  default=None,
                  help="set the source and type of peer rankings operation mode of neighbor selection (none|samehost|geoip|odd_even|sis|sis_simple)")
    
    op.add_option("-n", "--neighborselection_mode",
                  action="store", dest="mode_ns",
                  default=None,
                  help="set operation mode of neighbor selection (none|enable)")
    
    op.add_option("-p", "--peerselection_mode",
                  action="store", dest="mode_ps",
                  default=None,
                  help="set operation mode of unchoker's peer selection (none|enable)")
        
    randomid = random.randint(0, 999)
    op.add_option("-i", "--client_id",
                  action="store", dest="client_id",
                  default=str(randomid),
                  help="set client id")
    
    op.add_option("-c", "--config_file",
                  action="store", dest="config_file",
                  default="",
                  help="set config-file with -c <location of file>")
    
    default_download_dir = os.path.join(os.path.expanduser("~"), "Application Data", ".SwarmPlayer", "downloads")
    op.add_option("-d", "--directory",
                      action="store", dest="directory", default=default_download_dir,
                      help="Specifies the directory where torrents and downloads are stored (default is %s)." % (default_download_dir))

    default_state_dir = os.path.join(os.path.expanduser("~"), "Application Data", ".SwarmPlayer", "player_state")
    op.add_option("-s", "--state_dir",
                      action="store", dest="state_dir", default=default_state_dir,
                      help="Specifies the persistent state of the player will be stored (default is %s)." % (default_state_dir))                   
    
    
    if len(sys.argv) == 0:
        op.print_help()
    
    (options, args) = op.parse_args()
    
    # fill players config with default values
    internalConfig = {'rates': (None, None), 'sis_url': "localhost:8080/sis", "base_dir": os.path.abspath(options.state_dir)}

    sc = ClientConfiguration()
    
    if options.config_file == "":
        options.config_file = os.path.join(installdir, "config", "production", "default.cfg")
        
    sc._update_from_static_configuration(options.config_file)
    internalConfig['supporter_ips']=[sc.get_supporter_ip()]#currently there is just one!
    #sc.parse_static_data(options.config_file)

    # TODO: refactor and merge with client.py code
    if options.mode_ns is None:
        options.mode_ns = sc.get_ns_mode()
    if options.mode_ps is None:
        options.mode_ps = sc.get_peer_selection_mode()
    internalConfig['sis_url'] = sc.get_sis_url()
    x = sc.get_upload_limit()
    y = sc.get_download_limit()
    print >> sys.stderr, "Up/Down Limits are: (%s, %s)" % (x, y)
    internalConfig['rates'] = (x,y)
    internalConfig['max_uploads'] = sc.get_max_upload_slots_per_download()
    #internalConfig['torrent'] = sc.get_single_torrent()

    # base_dir is the state directory of the download!
    if not 'base_dir' in internalConfig:
        print "basedir not set, set it to 'temp'"
        internalConfig['base_dir'] = 'temp' + "/" + options.client_id

#    # remove old downloads and configs
#    configdir = internalConfig['base_dir'] + "/config"
#    print "configdir:", configdir
#    print "Removing old download-state"
#    #TODO: use shutil to remove subdirs
#    for root, dirs, files in os.walk(configdir, topdown=False):
#        for name in files:
#            os.remove(os.path.join(root, name))
#        for name in dirs:
#            os.rmdir(os.path.join(root, name))
#     
#    print "Loading", sys.argv
#    statedir = tempfile.mkdtemp()
    dldir = options.directory or tempfile.mkdtemp()
    internalConfig['dl_dir'] = dldir
    
    print "statedir: %s\n downloaddir: %s" % (internalConfig['base_dir'], dldir)
    
    
    logging.config.fileConfig(os.path.join(installdir, "config", "log_client.conf"))
    global logger
    logger = logging.getLogger("Player")
    #logger = get_testbed_logger("Player", "player.log")

    #use URL to update communicator
    sis_url = options.url or internalConfig['sis_url']
    
    # select ranking
    if options.ranking_source:
        sc.set_ranking_source(options_ranking_source)
    
    source = sc.get_ranking_source()
    
    ranking = RankingPolicy.selectRankingSource(source, sc)
        
    NeighborSelection.createMechanism(options.mode_ns, ranking, locality_pref=sc.get_locality_preference())         

    # TODO: don't use fully qualified path, do the import instead
    #SisClient.PeerSelection.PeerSelection.PeerSelection(options.mode_ps, sc)
    BiasedUnchoking.BiasedUnchoking(options.mode_ps, ranking)
    
    params = args
    if len(params) == 0:
        params = [""] 
    #is None or params == "":
    
    
            
    # SmoothIT-end
            
    if 'debug' in params:
        global ONSCREENDEBUG
        ONSCREENDEBUG = True
    if 'raw' in params:
        BaseLib.Video.VideoPlayer.USE_VLC_RAW_INTERFACE = True
    
    # Create single instance semaphore
    # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
    # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
    #
    # TEMPORARILY DISABLED on Linux
    if sys.platform != 'linux2':
        single_instance_checker = wx.SingleInstanceChecker("swarmplayer-" + wx.GetUserId())
    else:
        single_instance_checker = LinuxSingleInstanceChecker("swarmplayer")

    #KP_start
    for p in params:
        if p.endswith(constants.TORRENT_VOD_EXT):
            torrentfilename = p
            internalConfig['torrent'] = torrentfilename
    #_KP_end

    #print "[StartUpDebug]---------------- 1", time()-start_time
    if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
        i2ic = Instance2InstanceClient(I2I_LISTENPORT, 'START', torrentfilename)
        time.sleep(1)
        return

    print >> sys.stderr, "internalConfig=", internalConfig
    # Launch first single instance
    app = PlayerApp(0, params, single_instance_checker, installdir, internalConfig, sc)
    app.MainLoop()
    
    print >> sys.stderr, "Sleeping seconds to let other threads finish"
    time.sleep(2)

if __name__ == '__main__':
    try:
        run()
    except:
        if DEBUG:
            traceback.print_exc()

