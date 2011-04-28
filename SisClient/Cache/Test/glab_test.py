'''
Created on 01.09.2009

@author: jannik
'''

from subprocess import Popen
from time import *
from SisClient.Common import constants

DA167="glab167.g-lab.tu-darmstadt.de"
DA168="glab168.g-lab.tu-darmstadt.de"
DA169="glab169.g-lab.tu-darmstadt.de"
DA170="glab170.g-lab.tu-darmstadt.de"
DA171="glab171.g-lab.tu-darmstadt.de"
MU010="glab010.i4.tum.german-lab.de"
MU020="glab020.i4.tum.german-lab.de"
MU030="glab030.i4.tum.german-lab.de"
KA010="glab010.g-lab.uni-karlsruhe.de"
KA020="glab020.g-lab.uni-karlsruhe.de"
KA030="glab030.g-lab.uni-karlsruhe.de"
WU011="wine011.informatik.uni-wuerzburg.de"
WU013="wine013.informatik.uni-wuerzburg.de"
WU014="wine014.informatik.uni-wuerzburg.de"

baseDir = "BA"
webserver = "http://130.83.244.167:8888"
report_to = 'local_report'
file1 = "test.dat"
torrent1 = "test.dat"+constants.TORRENT_VOD_EXT
waiting_times = [5, 6, 3, 7, 7, 8, 6, 5, 9, 11, 7, 9, 3, 8, 3, 8, 7, 3, 8, 3, 8, 7, 7, 4, 9, 7, 4, 6, 7, 9, 8, 8, 7, 5, 6, 7, 10, 9, 10, 4, 11, 9, 9, 5, 5, 5, 3, 3, 9, 4, 4, 4, 5, 11, 3, 11, 4, 9, 6, 4, 6, 6, 10, 11, 11, 7, 3, 11, 11, 5, 8, 4, 10, 10, 5, 6, 11, 9, 7, 5, 5, 11, 7, 10, 10, 8, 9, 8, 3, 4, 9, 5, 3, 4, 7, 5, 3, 9, 8, 11, 8, 7, 4, 8, 7, 6, 8, 5, 8, 7, 3, 8, 7, 3, 9, 5, 3, 10, 10, 8, 11, 11, 4, 8, 3, 5, 5, 10, 5, 6, 7, 3, 3, 3, 4]
servers = [DA169,DA170,DA171,WU011,WU013,WU014,MU010,MU020,MU030]
all_servers = [DA167,DA168,DA169,DA170,DA171,WU011,WU013,WU014,MU010,MU020,MU030,KA010,KA020,KA030]

def start_tracker(server):
    piece_size = 256*1024
    cmd = "ssh tud_p2p@%s \"cd %s; sh tracker.sh --url=\"http://%s:8859/announce\" --directory=\"test/tracker\" --files_directory=\"test/files\" --piece_size=%d\"" % \
    (server, baseDir, server, piece_size)

    Popen(cmd, shell=True)
    
def setup_client(server, id, file, seeder=False):
    cmd = "ssh tud_p2p@%s \"cd %s/test/; rm -rf client%d; mkdir client%d" % \
    (server, baseDir, id, id)
    if seeder:
        cmd += "; cp files/%s client%d/" % (file, id)
    cmd += "\""
    Popen(cmd, shell=True)

def start_client(server, id, down, up, torrent, report=None, exit=False):
    cmd = "ssh tud_p2p@%s \"cd %s; sh client.sh --id=%d --download=%d --upload=%d --directory=\"test/client%d\" --single_torrent=\"test/torrents/%s\"" % \
    (server, baseDir, id, down, up, id, torrent)
    if not report == None:
        cmd += " --report_to=\"%s\"" % report
    if exit:
        cmd += " --exit_after_dl=True"
    cmd +="\""
    Popen(cmd, shell=True)
    
def setup_cache(server, id, file, seeder=False):
    cmd = "ssh tud_p2p@%s \"cd %s/test/; rm -rf cache%d; mkdir cache%d; cp -r torrents cache%d" % \
    (server, baseDir, id, id, id)
    if seeder:
        cmd += "; cp files/%s cache%d/" % (file, id)
    cmd += "\""
    Popen(cmd, shell=True)
    
def start_cache(server, id, port, down, up, report=None, exit=False):
    cmd = "ssh tud_p2p@%s \"cd %s; sh cache.sh --id=%d --port=%d --downlimit=%d --uplimit=%d --directory=\"test/cache%i\" --torrentdir=\"test/cache%d/torrents/\" --spacelimit=8000 --conlimit=500 --neighbour_selection_mode=\"local_cache\"" % \
    (server, baseDir, id, port, down, up, id, id)
    if not report == None:
        cmd += " --report_to=\"%s\"" % report
    cmd +="\""
    Popen(cmd, shell=True)    
    
def kill_python_processes():
    for server in all_servers:
        cmd = "ssh tud_p2p@%s killall python" % server
        Popen(cmd, shell=True)
    
def simple_test():
    start_tracker(DA167)
    sleep(5)
    #setup_cache(DA168, 1, file1, seeder=True)
    setup_client(DA168, 1, file1, seeder=True)
    setup_client(KA010, 2, file1)
    setup_client(MU010, 3, file1)
    sleep(5)
    #start_cache(DA168, 1, 10002, 100, 100, 'local_report')
    start_client(DA168, 1, 100, 100, torrent1, report_to)
    start_client(KA010, 2, 100, 100, torrent1, report_to)
    start_client(MU010, 3, 100, 100, torrent1, report_to)
    
    sleep(150)
    kill_python_processes([DA168,KA010,MU010])

def share_file():
    start_tracker(DA167)
    sleep(5)
    setup_cache(DA167, 1, file1, seeder=True)
    setup_client(DA168, 1, file1)
    setup_client(DA170, 1, file1)
    setup_client(DA171, 1, file1)
    setup_client(KA010, 1, file1)
    setup_client(KA020, 1, file1)
    setup_client(KA030, 1, file1)
    setup_client(MU010, 1, file1)
    setup_client(MU020, 1, file1)
    setup_client(MU030, 1, file1)
    setup_client(WU011, 1, file1)
    setup_client(WU013, 1, file1)
    setup_client(WU014, 1, file1)
    sleep(5)
    start_cache(DA167, 1, 10001, 1000, 1000)
    start_client(DA168, 1, 1000, 1000, torrent1)
    start_client(DA170, 1, 1000, 1000, torrent1) 
    start_client(DA171, 1, 1000, 1000, torrent1) 
    start_client(KA010, 1, 1000, 1000, torrent1) 
    start_client(KA020, 1, 1000, 1000, torrent1) 
    start_client(KA030, 1, 1000, 1000, torrent1) 
    start_client(MU010, 1, 1000, 1000, torrent1) 
    start_client(MU020, 1, 1000, 1000, torrent1) 
    start_client(MU030, 1, 1000, 1000, torrent1) 
    start_client(WU011, 1, 1000, 1000, torrent1) 
    start_client(WU013, 1, 1000, 1000, torrent1) 
    start_client(WU014, 1, 1000, 1000, torrent1) 
    
def test():
    start_tracker(DA167)
    sleep(5)
    setup_client(KA010, 201, file1, seeder=True)
    setup_client(KA020, 202, file1, seeder=True)
    setup_client(KA030, 203, file1, seeder=True)
    setup_client(KA010, 204, file1, seeder=True)
    setup_client(KA020, 205, file1, seeder=True)
    setup_client(KA030, 206, file1, seeder=True)
    start_client(KA010, 201, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA020, 202, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA030, 203, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA010, 204, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA020, 205, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA030, 206, 128, 128, torrent1, report_to)
    
    servers = [DA169,DA170,DA171,WU011,WU013,WU014,MU010,MU020,MU030]
    
    for i in range(0,9):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 64, 16, torrent1, report_to, exit)

def test_without_caches():
    start_tracker(DA167)
    sleep(5)
    setup_client(KA010, 201, file1, seeder=True)
    setup_client(KA020, 202, file1, seeder=True)
    setup_client(KA030, 203, file1, seeder=True)
    #setup_client(KA010, 204, file1, seeder=True)
    #setup_client(KA020, 205, file1, seeder=True)
    #setup_client(KA030, 206, file1, seeder=True)
    start_client(KA010, 201, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA020, 202, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA030, 203, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA010, 204, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA020, 205, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA030, 206, 128, 128, torrent1, report_to)
    
    for i in range(0,9):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    for i in range(9,135):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    sleep(600)
    
    kill_python_processes()
    
def test_with_caches():
    start_tracker(DA167)
    sleep(5)
    setup_client(KA010, 201, file1, seeder=True)
    setup_client(KA020, 202, file1, seeder=True)
    setup_client(KA030, 203, file1, seeder=True)
    #setup_client(KA010, 204, file1, seeder=True)
    #setup_client(KA020, 205, file1, seeder=True)
    #setup_client(KA030, 206, file1, seeder=True)
    start_client(KA010, 201, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA020, 202, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA030, 203, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA010, 204, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA020, 205, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA030, 206, 128, 128, torrent1, report_to)
    
    
    for i in range(0,9):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    setup_cache(DA171, 211, file1)
    setup_cache(MU030, 212, file1)
    setup_cache(WU014, 213, file1)
    start_cache(DA171, 211, 10011, 512, 512, report_to)
    sleep(3)
    start_cache(MU030, 212, 10012, 512, 512, report_to)
    sleep(3)
    start_cache(WU014, 213, 10013, 512, 512, report_to)
        
    for i in range(9,135):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    sleep(600)
    
    kill_python_processes()
    
   
    
def test_with_caches2():
    start_tracker(DA167)
    sleep(5)
    setup_client(KA010, 201, file1, seeder=True)
    setup_client(KA020, 202, file1, seeder=True)
    setup_client(KA030, 203, file1, seeder=True)
    #setup_client(KA010, 204, file1, seeder=True)
    #setup_client(KA020, 205, file1, seeder=True)
    #setup_client(KA030, 206, file1, seeder=True)
    start_client(KA010, 201, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA020, 202, 128, 128, torrent1, report_to)
    sleep(3)
    start_client(KA030, 203, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA010, 204, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA020, 205, 128, 128, torrent1, report_to)
    #sleep(3)
    #start_client(KA030, 206, 128, 128, torrent1, report_to)
    
    
    for i in range(0,9):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    setup_cache(DA171, 211, file1)
    #setup_cache(MU030, 212, file1, seeder=True)
    #setup_cache(WU014, 213, file1, seeder=True)
    start_cache(DA171, 211, 10011, 512, 512, report_to)
    #sleep(3)
    #start_cache(MU030, 212, 10012, 512, 512, report_to)
    #sleep(3)
    #start_cache(WU014, 213, 10013, 512, 512, report_to)
        
    for i in range(9,135):
        server = servers[i%9]
        setup_client(server,i+1,file1)
        sleep(waiting_times[i])
        exit = (i%3 == 0) 
        start_client(server, i+1, 128, 32, torrent1, report_to, exit)
        
    sleep(600)
    
    kill_python_processes()
    
def get_stats(path):
    FILE="/home/tud_p2p/BA/test/client*/*stats.txt"
    
    for server in all_servers:
        cmd = "scp tud_p2p@%s:/home/tud_p2p/BA/test/*/*stats.txt %s" % \
        (server, path)
        Popen(cmd, shell=True)
        cmd = "scp tud_p2p@%s:/home/tud_p2p/BA/test/client*/*CLIENT*.dat %s" % \
        (server, path)
        Popen(cmd, shell=True)
        cmd = "scp tud_p2p@%s:/home/tud_p2p/BA/test/cache*/*CACHE*.dat %s" % \
        (server, path)
        Popen(cmd, shell=True)
        
def clear():
    for server in all_servers:
        cmd="ssh tud_p2p@%s \"rm -rf BA/test/client*; rm -rf BA/test/cache*\"" % \
        (server)
        Popen(cmd, shell=True)

def tests():
  
    
    test_without_caches()
    sleep(15)
    get_stats("/home/jannik/results/TestIV/1/")
    sleep(60)
    clear()
    sleep(60)
    
    test_without_caches()
    sleep(15)
    get_stats("/home/jannik/results/TestIV/2/")
    sleep(60)
    clear()
    sleep(60)
    
    test_without_caches()
    sleep(15)
    get_stats("/home/jannik/results/TestIV/3/")
    sleep(60)
    clear()
    sleep(60)
    
    test_without_caches()
    sleep(15)
    get_stats("/home/jannik/results/TestIV/4/")
    sleep(60)
    clear()
    
    

if __name__ == "__main__":
    tests()
    #test_without_caches()
    #test_with_caches2()
    #share_file()
    #simple_test()
    #test()
    
