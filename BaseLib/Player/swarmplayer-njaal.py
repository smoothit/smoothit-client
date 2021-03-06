# Written by Arno Bakker, Choopan RATTANAPOKA, Jie Yang
# see LICENSE.txt for license information
#
# TODO: 
# * set 'download_slice_size' to 32K, such that pieces are no longer
#   downloaded in 2 chunks. This particularly avoids a bad case where you
#   kick the source: you download chunk 1 of piece X
#   from lagging peer and download chunk 2 of piece X from source. With the piece
#   now complete you check the sig. As the first part of the piece is old, this
#   fails and we kick the peer that gave us the completing chunk, which is the 
#   source.
#
#   Note that the BT spec says: 
#   "All current implementations use 2 15 , and close connections which request 
#   an amount greater than 2 17." http://www.bittorrent.org/beps/bep_0003.html
#
#   So it should be 32KB already. However, the BitTorrent (3.4.1, 5.0.9), 
#   BitTornado and Azureus all use 2 ** 14 = 16KB chunks.
#
# - See if we can use stream.seek() to optimize SwarmPlayer as well (see SwarmPlugin)

import os
import sys
import time
import tempfile
from traceback import print_exc
from cStringIO import StringIO
from threading import Thread

from base64 import encodestring

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
from BaseLib.Core.Utilities.timeouturlopen import urlOpenTimeout

from BaseLib.Video.defs import * 
from BaseLib.Video.VideoPlayer import VideoPlayer, VideoChooser  
from BaseLib.Video.utils import videoextdefaults
from BaseLib.Utilities.LinuxSingleInstanceChecker import *
from BaseLib.Utilities.Instance2Instance import Instance2InstanceClient

from BaseLib.Player.PlayerVideoFrame import VideoFrame
from BaseLib.Player.BaseApp import BaseApp

from BaseLib.Core.Status import *

DEBUG = True
ONSCREENDEBUG = False
ALLOW_MULTIPLE = False

PLAYER_VERSION = '1.1.0'

I2I_LISTENPORT = 57894
PLAYER_LISTENPORT = 8620
VIDEOHTTP_LISTENPORT = 6879

class PlayerApp(BaseApp):
    def __init__(self, redirectstderrout, appname, params, single_instance_checker, installdir, i2iport, sport):

        BaseApp.__init__(self, redirectstderrout, appname, params, single_instance_checker, installdir, i2iport, sport)

        self.said_start_playback = False
        self.decodeprogress = 0

        
    def OnInit(self):
        try:
            # If already running, and user starts a new instance without a URL 
            # on the cmd line
            if not ALLOW_MULTIPLE and self.single_instance_checker.IsAnotherRunning():
                print >> sys.stderr,"main: Another instance running, no URL on CMD, asking user"
                torrentfilename = self.select_torrent_from_disk()
                if torrentfilename is not None:
                    i2ic = Instance2InstanceClient(I2I_LISTENPORT,'START',torrentfilename)
                    return False

            # Do common initialization
            BaseApp.OnInitBase(self)
        
            # Fire up the VideoPlayer, it abstracts away whether we're using
            # an internal or external video player.
            self.videoplayer = VideoPlayer.getInstance(httpport=VIDEOHTTP_LISTENPORT)
            playbackmode = PLAYBACKMODE_INTERNAL
            self.videoplayer.register(self.utility,preferredplaybackmode=playbackmode)
            
            # Open video window
            self.start_video_frame()

            # Load torrent
            if self.params[0] != "":
                torrentfilename = self.params[0]
                
                # TEST: just play video file
                #self.videoplayer.play_url(torrentfilename)
                #return True
                
            else:
                torrentfilename = self.select_torrent_from_disk()
                if torrentfilename is None:
                    print >>sys.stderr,"main: User selected no file"
                    self.OnExit()
                    return False


            # Start download
            if not self.select_file_start_download(torrentfilename):
                
                self.OnExit()
                return False

            return True
        
        except Exception,e:
            print_exc()
            self.show_error(str(e))
            self.OnExit()
            return False


    def start_video_frame(self):
        self.videoFrame = PlayerFrame(self,self.appname)
        self.Bind(wx.EVT_CLOSE, self.videoFrame.OnCloseWindow)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.videoFrame.OnCloseWindow)
        self.Bind(wx.EVT_END_SESSION, self.videoFrame.OnCloseWindow)
        self.videoFrame.show_videoframe()

        if self.videoplayer is not None:
            self.videoplayer.set_videoframe(self.videoFrame)
        self.said_start_playback = False
        
        
    def select_torrent_from_disk(self):
        dlg = wx.FileDialog(None, 
                            self.appname+': Select torrent to play', 
                            '', # default dir
                            '', # default file
                            'TSTREAM and TORRENT files (*.tstream;*.torrent)|*.tstream;*.torrent', 
                            wx.OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        else:
            filename = None
        dlg.Destroy()
        return filename


    def select_file_start_download(self,torrentfilename):
        tdef = TorrentDef.load(torrentfilename)
        print >>sys.stderr,"main: Starting download, infohash is",`tdef.get_infohash()`

        status = Status.get_status_holder("LivingLab")
        status.create_status_element("swarm_id", encodestring(tdef.infohash).replace("\n",""))
        event = status.create_event("ClosedSwarm")

        poa = None
        if tdef.get_cs_keys():
            event.add_value("CS_has_keys")

            from BaseLib.Core.ClosedSwarm import ClosedSwarm,Tools,PaymentIntegration
            # Can choose between two POA reading functions now
            # TODO: Should likely not use the __single here... :)
            try:
                #s = Session(ignore_singleton=True) # GET THIS FROM SOMEWHERE - Why is there not a "getSingleton()" here???
                s = Session.get_instance()
                poa = ClosedSwarm.trivial_get_poa(Session.get_default_state_dir(),
                                                  s.get_permid(),
                                                  tdef.infohash)
                
                poa.verify()
                if not poa.torrent_id == tdef.infohash:
                    event.add_value("CS_wrong_POA")
                    raise Exception("Local POA not valid for this swarm")
                print >>sys.stderr,"Got valid POA"
                event.add_value("CS_valid_POA")
            except Exception,e:
                print >>sys.stderr,"Reading POA:",e
                # Do not have the POA!
                try:
                    while True:
                        my_id = encodestring(s.get_permid()).replace("\n","")
                        swarm_id = encodestring(tdef.infohash).replace("\n","")
                        
                        poa = PaymentIntegration.wx_get_poa("http://seer2.itek.norut.no:9090", 
                                                            swarm_id, 
                                                            my_id, 
                                                            swarm_title=tdef.get_name())

                        #poa = Tools.wx_get_http_poa("http://tracker.farnorthlivinglab.no:8080/", swarm_id, my_id)
                        #poa = Tools.wx_get_poa()
                        try:
                            valid_ok = poa.verify()
                            if not poa.torrent_id == tdef.infohash:
                                event.add_value("CS_wrong_POA")
                                raise Exception("POA not valid for this swarm")
                        except Exception,e:
                            print >>sys.stderr,"Selecting POA:",e
                            continue

                        event.add_value("CS_valid_POA")
                        event.add_value("CS_downloaded_POA")
                        # Save it for future reference
                        try:
                            ClosedSwarm.trivial_save_poa(Session.get_default_state_dir(),
                                                         s.get_permid(),
                                                         tdef.infohash,
                                                         poa)
                        except Exception,e:
                            print >>sys.stderr,"Could not save POA:",e
                            
                        break

                except Exception,e:
                    print >>sys.stderr,"Error selecting POA:",e
                    event.add_value("CS_no_POA")
                    poa = None
                    pass # Continue with no poa

        status.add_event(event)

        # Select which video to play (if multiple)
        videofiles = tdef.get_files(exts=videoextdefaults)
        print >>sys.stderr,"main: Found video files",videofiles
        
        if len(videofiles) == 0:
            print >>sys.stderr,"main: No video files found! Let user select"
            # Let user choose any file
            videofiles = tdef.get_files(exts=None)
            
        if len(videofiles) > 1:
            selectedvideofile = self.ask_user_which_video_from_torrent(videofiles)
            if selectedvideofile is None:
                print >>sys.stderr,"main: User selected no video"
                return False
            dlfile = selectedvideofile
        else:
            dlfile = videofiles[0]

        # Arno: 2008-7-15: commented out, just stick with old ABC-tuned 
        # settings for now
        #dcfg.set_max_conns_to_initiate(300)
        #dcfg.set_max_conns(300)
        
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

        # Display name and thumbnail
        cname = tdef.get_name_as_unicode()
        if len(videofiles) > 1:
            cname += u' - '+bin2unicode(dlfile)
        self.videoplayer.set_content_name(u'Loading: '+cname)
        
        try:
            [mime,imgdata] = tdef.get_thumbnail()
            if mime is not None:
                f = StringIO(imgdata)
                img = wx.EmptyImage(-1,-1)
                img.LoadMimeStream(f,mime,-1)
                self.videoplayer.set_content_image(img)
            else:
                self.videoplayer.set_content_image(None)
        except:
            print_exc()


        # Start actual download
        self.start_download(tdef,dlfile,poa)
        return True



    def ask_user_which_video_from_torrent(self,videofiles):
        dlg = VideoChooser(self.videoFrame,self.utility,videofiles,title=self.appname,expl='Select which file to play')
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            index = dlg.getChosenIndex()
            filename = videofiles[index]
        else:
            filename = None
        dlg.Destroy()
        return filename


    # ARNOTODO: see how VideoPlayer manages stopping downloads
    
    def sesscb_vod_event_callback(self,d,event,params):
        self.videoplayer.sesscb_vod_event_callback(d,event,params)
        
        
    def get_supported_vod_events(self):
        return self.videoplayer.get_supported_vod_events()


    #
    # Remote start of new torrents
    #
    def i2ithread_readlinecallback(self,ic,cmd):
        """ Called by Instance2Instance thread """
        
        print >>sys.stderr,"main: Another instance called us with cmd",cmd
        ic.close()
        
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
            wx.CallAfter(self.remote_start_download,torrentfilename)

    def remote_start_download(self,torrentfilename):
        """ Called by GUI thread """
        self.videoplayer.stop_playback(reset=True)

        self.remove_downloads_in_vodmode_if_not_complete()
        self.select_file_start_download(torrentfilename)


    #
    # Display stats in videoframe
    #
    def gui_states_callback(self,dslist,haspeerlist):
        """ Override BaseApp """
        (playing_dslist,totalhelping,totalspeed) = BaseApp.gui_states_callback(self,dslist,haspeerlist)
        
        # Don't display stats if there is no video frame to show them on.
        if self.videoFrame is None:
            return
        elif len(playing_dslist) > 0:
            ds = playing_dslist[0] # only single playing Download at the moment in swarmplayer 
            self.display_stats_in_videoframe(ds,totalhelping,totalspeed)


    def display_stats_in_videoframe(self,ds,totalhelping,totalspeed):
        # Display stats for currently playing Download
        
        videoplayer_mediastate = self.videoplayer.get_state()
        #print >>sys.stderr,"main: Stats: VideoPlayer state",videoplayer_mediastate
        
        [topmsg,msg,self.said_start_playback,self.decodeprogress] = get_status_msgs(ds,videoplayer_mediastate,self.appname,self.said_start_playback,self.decodeprogress,totalhelping,totalspeed)
        # Display helping info on "content name" line.
        self.videoplayer.set_content_name(topmsg)

        # Update status msg and progress bar
        self.videoplayer.set_player_status_and_progress(msg,ds.get_pieces_complete())
        
        # Toggle save button
        self.videoplayer.set_save_button(ds.get_status() == DLSTATUS_SEEDING, self.save_video_copy)    
            
        if False: # Only works if the sesscb_states_callback() method returns (x,True)
            peerlist = ds.get_peerlist()
            print >>sys.stderr,"main: Connected to",len(peerlist),"peers"
            for peer in peerlist:
                print >>sys.stderr,"main: Connected to",peer['ip'],peer['uprate'],peer['downrate']


    def videoserver_set_status_guicallback(self,status):
        """ Override BaseApp """
        if self.videoFrame is not None:
            self.videoFrame.set_player_status(status)

    #
    # Save button logic
    #
    def save_video_copy(self):
        # Save a copy of playing download to other location

        for d2 in self.downloads_in_vodmode:
            # only single playing Download at the moment in swarmplayer
            d = d2
        dest_files = d.get_dest_files()  
        dest_file = dest_files[0] # only single file at the moment in swarmplayer
        savethread_callback_lambda = lambda:self.savethread_callback(dest_file)
        
        t = Thread(target = savethread_callback_lambda)
        t.setName( self.appname+"Save"+t.getName() )
        t.setDaemon(True)
        t.start()
    
    def savethread_callback(self,dest_file):
        
        # Save a copy of playing download to other location
        # called by new thread from self.save_video_copy
        try:
            if sys.platform == 'win32':
                # Jelle also goes win32, find location of "My Documents"
                # see http://www.mvps.org/access/api/api0054.htm
                from win32com.shell import shell
                pidl = shell.SHGetSpecialFolderLocation(0,0x05)
                defaultpath = shell.SHGetPathFromIDList(pidl)
            else:
                defaultpath = os.path.expandvars('$HOME')
        except Exception, msg:
            defaultpath = ''
            print_exc()

        dest_file_only = os.path.split(dest_file[1])[1]
        
        print >> sys.stderr, 'Defaultpath:', defaultpath, 'Dest:', dest_file
        dlg = wx.FileDialog(self.videoFrame, 
                            message = self.utility.lang.get('savemedia'), 
                            defaultDir = defaultpath, 
                            defaultFile = dest_file_only,
                            wildcard = self.utility.lang.get('allfileswildcard') + ' (*.*)|*.*', 
                            style = wx.SAVE)
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

    # On Exit

    def clear_session_state(self):
        """ Try to fix apps by doing hard reset. Called from systray menu """
        try:
            self.videoplayer.stop_playback()
        except:
            print_exc()
        BaseApp.clear_session_state(self)



def get_status_msgs(ds,videoplayer_mediastate,appname,said_start_playback,decodeprogress,totalhelping,totalspeed):

    intime = "Not playing for quite some time."
    ETA = ((60 * 15, "Playing in less than 15 minutes."),
           (60 * 10, "Playing in less than 10 minutes."),
           (60 * 5, "Playing in less than 5 minutes."),
           (60, "Playing in less than a minute."))

    topmsg = ''
    msg = ''

    logmsgs = ds.get_log_messages()
    logmsg = None
    if len(logmsgs) > 0:
        print >>sys.stderr,"main: Log",logmsgs[0]
        logmsg = logmsgs[-1][1]
        
    preprogress = ds.get_vod_prebuffering_progress()
    playable = ds.get_vod_playable()
    t = ds.get_vod_playable_after()

    # Instrumentation
    # Status elements (reported periodically):
    #   playable: True if playable
    #   prebuffering: float of percentage full?
    #
    # Events:
    #   failed_after: Failed to play after X seconds (since starting to play)
    #   playable_in: Started playing after X seconds
    status = Status.get_status_holder("LivingLab")

    s_play = status.get_or_create_status_element("playable", False)
    if playable:
        if preprogress < 1.0:
            if s_play.get_value() == True:
                global START_TIME
                status.create_and_add_event("failed_after", [time.time() - START_TIME])
                START_TIME = time.time()
                
            s_play.set_value(False)

        elif s_play.get_value() == False:
            s_play.set_value(True)
            global START_TIME
            status.create_and_add_event("playable_in", [time.time() - START_TIME])
            START_TIME = time.time()

    elif preprogress < 1.0:
        status.get_or_create_status_element("prebuffering").set_value(preprogress)
    # /Instrumentation
    
    intime = ETA[0][1]
    for eta_time, eta_msg in ETA:
        if t > eta_time:
            break
        intime = eta_msg
    
    #print >>sys.stderr,"main: playble",playable,"preprog",preprogress
    #print >>sys.stderr,"main: ETA is",t,"secs"
    # if t > float(2 ** 30):
    #     intime = "inf"
    # elif t == 0.0:
    #     intime = "now"
    # else:
    #     h, t = divmod(t, 60.0*60.0)
    #     m, s = divmod(t, 60.0)
    #     if h == 0.0:
    #         if m == 0.0:
    #             intime = "%ds" % (s)
    #         else:
    #             intime = "%dm:%02ds" % (m,s)
    #     else:
    #         intime = "%dh:%02dm:%02ds" % (h,m,s)
            
    #print >>sys.stderr,"main: VODStats",preprogress,playable,"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    if ds.get_status() == DLSTATUS_HASHCHECKING:
        genprogress = ds.get_progress()
        pstr = str(int(genprogress*100))
        msg = "Checking already downloaded parts "+pstr+"% done"
    elif ds.get_status() == DLSTATUS_STOPPED_ON_ERROR:
        msg = 'Error playing: '+str(ds.get_error())
    elif ds.get_progress() == 1.0:
        msg = ''
    elif playable:
        if not said_start_playback:
            msg = "Starting playback..."
            
        if videoplayer_mediastate == MEDIASTATE_STOPPED and said_start_playback:
            if totalhelping == 0:
                topmsg = u"Please leave the "+appname+" running, this will help other "+appname+" users to download faster."
            else:
                topmsg = u"Helping "+str(totalhelping)+" "+appname+" users to download. Please leave it running in the background."
                
            # Display this on status line
            # TODO: Show balloon in systray when closing window to indicate things continue there
            msg = ''
            
        elif videoplayer_mediastate == MEDIASTATE_PLAYING:
            said_start_playback = True
            # It may take a while for VLC to actually start displaying
            # video, as it is trying to tune in to the stream (finding
            # I-Frame). Display some info to show that:
            #
            cname = ds.get_download().get_def().get_name_as_unicode()
            topmsg = u'Decoding: '+cname+' '+str(decodeprogress)+' s'
            decodeprogress += 1
            msg = ''
        elif videoplayer_mediastate == MEDIASTATE_PAUSED:
            # msg = "Buffering... " + str(int(100.0*preprogress))+"%" 
            msg = "Buffering... " + str(int(100.0*preprogress))+"%. " + intime
        else:
            msg = ''
            
    elif preprogress != 1.0:
        pstr = str(int(preprogress*100))
        npeers = ds.get_num_peers()
        npeerstr = str(npeers)
        if npeers == 0 and logmsg is not None:
            msg = logmsg
        elif npeers == 1:
            msg = "Prebuffering "+pstr+"% done (connected to 1 person). " + intime
        else:
            msg = "Prebuffering "+pstr+"% done (connected to "+npeerstr+" people). " + intime
            
        try:
            d = ds.get_download()
            tdef = d.get_def()
            videofiles = d.get_selected_files()
            if len(videofiles) >= 1:
                videofile = videofiles[0]
            else:
                videofile = None
            if tdef.get_bitrate(videofile) is None:
                msg += ' This video may not play properly because its bitrate is unknown'
        except:
            print_exc()
    else:
        # msg = "Waiting for sufficient download speed... "+intime
        msg = 'Waiting for sufficient download speed... ' + intime
        
    global ONSCREENDEBUG
    if msg == '' and ONSCREENDEBUG:
        uptxt = "up %.1f" % (totalspeed[UPLOAD])
        downtxt = " down %.1f" % (totalspeed[DOWNLOAD])
        peertxt = " peer %d" % (totalhelping)
        msg = uptxt + downtxt + peertxt

    return [topmsg,msg,said_start_playback,decodeprogress]



class PlayerFrame(VideoFrame):
    def __init__(self,parent,appname):
        VideoFrame.__init__(self,parent,parent.utility,appname+' '+PLAYER_VERSION,parent.iconpath,parent.videoplayer.get_vlcwrap(),parent.logopath)
        self.parent = parent
        self.closed = False

        dragdroplist = FileDropTarget(self.parent)
        self.SetDropTarget(dragdroplist)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    def OnCloseWindow(self, event = None):
        
        print >>sys.stderr,"main: ON CLOSE WINDOW"

        # TODO: first event.Skip does not close window, second apparently does
        # Check how event differs

        if event is not None:
            nr = event.GetEventType()
            lookup = { wx.EVT_CLOSE.evtType[0]: "EVT_CLOSE", wx.EVT_QUERY_END_SESSION.evtType[0]: "EVT_QUERY_END_SESSION", wx.EVT_END_SESSION.evtType[0]: "EVT_END_SESSION" }
            if nr in lookup: 
                nr = lookup[nr]
            print >>sys.stderr,"main: Closing due to event ",nr
            event.Skip()
        else:
            print >>sys.stderr,"main: Closing untriggered by event"

        # This gets called multiple times somehow
        if not self.closed:
            self.closed = True
            self.parent.videoFrame = None

            self.parent.videoplayer.stop_playback()
            self.parent.remove_downloads_in_vodmode_if_not_complete()
            self.parent.restart_other_downloads()
            
        print >>sys.stderr,"main: Closing done"
        # TODO: Show balloon in systray when closing window to indicate things continue there


class FileDropTarget(wx.FileDropTarget):
    """ To enable drag and drop of .tstream to window """
 
    def __init__(self,app):
        wx.FileDropTarget.__init__(self) 
        self.app = app
      
    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            self.app.remote_start_download(filename)
        return True


                
        
##############################################################
#
# Main Program Start Here
#
##############################################################
def run_playerapp(appname,params = None):

    global START_TIME
    START_TIME = time.time()
    
    if params is None:
        params = [""]
    
    if len(sys.argv) > 1:
        params = sys.argv[1:]
    
    if 'debug' in params:
        global ONSCREENDEBUG
        ONSCREENDEBUG=True
    if 'raw' in params:
        Tribler.Video.VideoPlayer.USE_VLC_RAW_INTERFACE = True

    
    # Create single instance semaphore
    # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
    # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
    #
    siappname = appname.lower() # For backwards compatibility
    if sys.platform != 'linux2':
        single_instance_checker = wx.SingleInstanceChecker(siappname+"-"+ wx.GetUserId())
    else:
        single_instance_checker = LinuxSingleInstanceChecker(siappname)

    #print "[StartUpDebug]---------------- 1", time()-start_time
    if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
        if params[0] != "":
            torrentfilename = params[0]
            i2ic = Instance2InstanceClient(I2I_LISTENPORT,'START',torrentfilename)
            time.sleep(1)
            return
        
    arg0 = sys.argv[0].lower()
    if arg0.endswith('.exe'):
        installdir = os.path.abspath(os.path.dirname(sys.argv[0]))
    else:
        installdir = os.getcwd()  

    # Launch first single instance
    app = PlayerApp(0, appname, params, single_instance_checker, installdir, I2I_LISTENPORT, PLAYER_LISTENPORT)

    # Setup the statistic reporter while waiting for proper integration
    status = Status.get_status_holder("LivingLab")
    s = Session.get_instance()
    id = encodestring(s.get_permid()).replace("\n","")
    reporter = LivingLabReporter.LivingLabPeriodicReporter("Living lab CS reporter", 300, id) # Report every 5 minutes 
    status.add_reporter(reporter)

    app.MainLoop()

    reporter.stop()
    
    print >>sys.stderr,"Sleeping seconds to let other threads finish"
    time.sleep(2)
    
    if not ALLOW_MULTIPLE:
        del single_instance_checker


if __name__ == '__main__':

    run_playerapp("SwarmPlayer")

