from SisClient.Common import constants
import os
import sys
import shutil
import time

from subprocess import Popen

from BaseLib.Core.TorrentDef import TorrentDef

from SisClient.Testbed.Utils.utils import FileUtils

__HEADLESS_SCRIPT__ = os.path.join(os.getcwd(), 'SisClient', 'Testbed', 'client.py')
__TRACKER_SCRIPT__ = os.path.join(os.getcwd(), 'SisClient', 'Testbed', 'tracker.py')
__VODCLIENT_SCRIPT__ = os.path.join(os.getcwd(), 'SisClient', 'Tools', 'vodclient.py')
__PLAYTIME_SCRIPT__ = os.path.join(os.getcwd(), 'SisClient', 'Tools', 'add_playtime.py')
__USE_SHELL__ = False


active_procs = []
vodclient_dirs = []
tracker_proc = None
seeder_proc = None

current_client = 0

def check_dependencies():
    file_dependencies = [ __HEADLESS_SCRIPT__, __TRACKER_SCRIPT__, __VODCLIENT_SCRIPT__, __DOWNLOAD__ ]
    for file in file_dependencies:
        if not os.access(file, os.F_OK):
            print >>sys.stderr, 'Missing file dependency: %s' % file
            print >>sys.stderr, 'Exiting.'
            sys.exit(1)
            
def add_playtime_to_torrent(torrent):
    global __TORRENT__, __TORRENT_NEW__
    shellcmd = 'python %s %s %s' % (__PLAYTIME_SCRIPT__,
                                    __TORRENT__,
                                    __DOWNLOAD__)
    proc = Popen(shellcmd.split(' '), shell=__USE_SHELL__)
    proc.wait()
    
def prepare_scenario():
    global __DOWNLOAD__
    os.makedirs('basic_scenario_files')
    shutil.copyfile(__DOWNLOAD__, os.path.join('basic_scenario_files', FileUtils.get_relative_filename(__DOWNLOAD__)))

def spawn_tracker():
    global tracker_proc, __TORRENT__, __TRACKER_SCRIPT__
    os.makedirs('basic_scenario_tracker')
    
    shellcmd = 'python %s -u http://localhost:8859/announce -d basic_scenario_tracker -f basic_scenario_files' % __TRACKER_SCRIPT__
    #while not os.path.exists(__TORRENT__):
    #    print "wait for %s torrent to be created!" % __TORRENT__
    #    time.sleep(1)
    #shutil.copyfile(__TORRENT__, os.path.join('basic_scenario_tracker', __TORRENT__))
    tracker_proc = Popen(shellcmd.split(' '), shell=__USE_SHELL__)

def spawn_headless(ulrate):
    global seeder_proc, __TORRENT__, __DOWNLOAD__, __HEADLESS_SCRIPT__
    os.makedirs('basic_scenario_seeder')
    shutil.copyfile(__TORRENT__, os.path.join('basic_scenario_seeder', __TORRENT__))
    shutil.copyfile(__DOWNLOAD__, os.path.join('basic_scenario_seeder', FileUtils.get_relative_filename(__DOWNLOAD__)))
    shellcmd = 'python %s -p 50000 -d basic_scenario_seeder -x %i --single_torrent=%s' % (
            __HEADLESS_SCRIPT__, ulrate, os.path.join('basic_scenario_seeder', __TORRENT__))
    seeder_proc = Popen(shellcmd.split(' '), shell=__USE_SHELL__)

def spawn_vodclient(ulrate, dlrate):
    global __TORRENT_NEW__, __VODCLIENT_SCRIPT__, current_client, active_procs
    current_client += 1
    vodclient_directory = 'basic_scenario_vodclient%i' % current_client
    logfile = 'vodclient%s.log' % str(current_client)
    os.makedirs(vodclient_directory)
    shutil.copyfile(__TORRENT_NEW__, os.path.join(vodclient_directory, __TORRENT_NEW__))
    shellcmd = 'python %s --torrent=%s --directory=%s --port=%i -x %i -y %i -l %s' % (__VODCLIENT_SCRIPT__,
            os.path.join(vodclient_directory, __TORRENT_NEW__),
            vodclient_directory,
            current_client*2 + 10000,
            dlrate, ulrate,
            logfile)
    proc = Popen(shellcmd.split(' '), shell=__USE_SHELL__)
    active_procs.append(proc)

def cleanup():
    global vodclient_dirs, tracker_proc, active_procs, seeder_proc
    print >>sys.stderr, 'Killing remaining processes...'
    tracker_proc.kill()
    seeder_proc.kill()
    seeder_proc.terminate()
    for vodclient_proc in active_procs:
        vodclient_proc.kill()
    print >>sys.stderr, 'Removing directories...'
    FileUtils.remove_directory_recursively('basic_scenario_tracker')
    FileUtils.remove_directory_recursively('basic_scenario_seeder')
    FileUtils.remove_directory_recursively('basic_scenario_files')
    for dir in vodclient_dirs:
        os.removedirs(dir)
    os.unlink(__TORRENT_NEW__)
#___________________________________________________________________________________________________
# MAIN

def main():
    global __TORRENT__, __TORRENT_NEW__, __DOWNLOAD__, active_procs
    
    if len(sys.argv[1:]) != 1:
        print >>sys.stderr, 'Usage: %s <full download>' % sys.argv[0]
        sys.exit(1)
        
    __DOWNLOAD__ = sys.argv[1]
    __TORRENT__ = FileUtils.get_relative_filename(__DOWNLOAD__) + constants.TORRENT_DOWNLOAD_EXT
    __TORRENT_NEW__ = __TORRENT__ + '-new'
    
    check_dependencies()
    prepare_scenario()
    
    start_ts = time.time()
    last_vodclient_spawned = time.time()-30.0
    print >>sys.stderr, 'Spawning tracker process...'
    spawn_tracker()
    time.sleep(10)
    print >>sys.stderr, 'Fetching torrent from tracker...'
    shutil.copyfile(os.path.join('basic_scenario_tracker', __TORRENT__), __TORRENT__)
    print >>sys.stderr, 'Adding playtime information to %s' % __TORRENT__
    add_playtime_to_torrent(__TORRENT__)
    tdef = TorrentDef.load(__TORRENT_NEW__)
    bitrate = tdef.get_bitrate()
    print >>sys.stderr, 'Bitrate is: %i' % bitrate
    print >>sys.stderr, 'Spawning seeder process...'
    spawn_headless(bitrate*4)
    FINISH_TIME = 90 # experiment duration in seconds
    count = 0
    while (time.time() - start_ts <= FINISH_TIME):
        if count == 10:
            count = 0
            print >>sys.stderr, 'Scenario progress '+str(time.time() - start_ts)
        count+=1
        # remove finished vodclient processes
        active_procs = [p for p in active_procs if p.poll() == None]
        # check if we have to spawn a new vodclient
        ts = time.time()
        if ts - last_vodclient_spawned >= 30.0 and len(active_procs) < 2:
            print >>sys.stderr, '%s: Spawning new vod client... experiment progress is %f' % (str(ts), ts/start_ts*100)
            spawn_vodclient(bitrate/4, bitrate)
            last_vodclient_spawned = ts
        time.sleep(1.0)
    print >>sys.stderr, 'Emulation finished, finish and exit...'
    cleanup()
    os._exit(0)

if __name__ == "__main__":
    main()