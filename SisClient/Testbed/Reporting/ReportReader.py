import os
import optparse
import socket

''' This package can be used to process all statistic files that are generated
    by the clients.
'''

client_info = []

def read_statistic_file(file):
    handler = open(file, "r")
    stats = dict() 
    (key, value) = readStats(handler)
    
    while not key == "peer_info":
        stats[key] = value
        (key, value) = readStats(handler)
    
    peer_infos = []
    peer_info = readPeerInfo(handler)
    
    while not peer_info == None:
        peer_infos.append({
                           "ip":        peer_info[0],
                           "id":        peer_info[1],
                           "down_total":peer_info[2],
                           "up_total":  peer_info[3]
                           })
        peer_info = readPeerInfo(handler)
        
        
    return (stats, peer_infos)
    
def readStats(handler):
    line = handler.readline().strip()
    if line == "peer info:":
        return ("peer_info", None)
    split = line.split('=')
    return (split[0], split[1])

def readPeerInfo(handler):
    line = handler.readline().strip()
    if line == "":
        return None
    split = line.split(' ')
    return split

def read_client_stats(directory):
    files = os.listdir(directory)
    
    for file in files:
        if file.endswith("stats.txt"):
            filepath = os.path.join(options.directory, file)
            (stats, peer_infos) = read_statistic_file(filepath)
            global client_info
            client_info.append((stats, peer_infos))
                    
def process_client_info(save_dir):
    download_times = open(os.path.join(save_dir, "download_times.dat"),"w")

    stats = dict()
    dl_times_total = dict()
    traffic = dict()
    finished = dict()
    unfinished = dict()
    start = 0.0
    end = 0.0
    for (peer_stats, peer_infos) in client_info:
       # try:
       #     if start == 0.0 or start > float(peer_stats['seeding_start']):
       #         start = float(peer_stats['seeding_start'])
       #     if end == 0.0 or end < float(peer_stats['seeding_finished']):
       #         end = float(peer_stats['seeding_finished'])
       # except:
       #     pass
       # try:
       #     if start > peer_stats['leeching_start']:
       #         start = float(peer_stats['leeching_start'])
       #     if end < peer_stats['leeching_start']:
       #         end = float(peer_stats['leeching_finished'])
       # except:
       #     pass
            
        hostname = get_hostname(peer_stats['IP'])
        
        if not stats.has_key(hostname):
            stats[hostname] = dict()
            stats[hostname]['dl_times_total'] = 0.0
            stats[hostname]['traffic'] = {'local_down': 0.0, 'local_up': 0.0, 'external_down': 0.0, 'external_up': 0.0}
            stats[hostname]['finished'] = 0
            stats[hostname]['unfinished'] = 0
        
        local_stats = stats[hostname]
        
        if float(peer_stats['complete']) == 100.0:
            if float(peer_stats['dl_time']) > 0:
                local_stats['finished'] += 1
                download_times.write(peer_stats['dl_time']+"\n")
                local_stats['dl_times_total'] += float(peer_stats['dl_time']) 
        else:
            local_stats['unfinished'] += 1  
                 
        for peer_info in peer_infos:
            peer_host = get_hostname(peer_info['ip'])
            if peer_host == hostname:
                local_stats['traffic']['local_down'] += float(peer_info['down_total'])
                local_stats['traffic']['local_up'] += float(peer_info['up_total'])
            else:
                local_stats['traffic']['external_down'] += float(peer_info['down_total'])
                local_stats['traffic']['external_up'] += float(peer_info['up_total'])
    
    download_times.close()
                
    return (stats, start, end)

def write_stats(save_dir, stats):
    statsfile = open(os.path.join(save_dir, "statistics.txt"),"w")
    
    for (host, info) in stats.items():
        if info['finished'] > 0:
            avg_dl_time = info['dl_times_total'] / info['finished']
        else:
            avg_dl_time = 0
        

        statsfile.write(host+":\n")
        statsfile.write("finished: %d\n" % info['finished'])
        statsfile.write("unfinished: %d\n" % info['unfinished'])
        statsfile.write("avg_dl_time: %f\n" % avg_dl_time)
        statsfile.write("local_down: %fMB \n" % (float(info['traffic']['local_down']) / 1024))
        statsfile.write("local_up: %fMB \n" % (float(info['traffic']['local_up']) / 1024))
        statsfile.write("external_down: %fMB \n" % (float(info['traffic']['external_down']) / 1024))
        statsfile.write("external_up: %fMB \n" % (float(info['traffic']['external_up']) / 1024))
        statsfile.write("\n")
    
    statsfile.close()
    
def write_seeder_leecher(start, end, save_dir):
    
    seeder_leecher_file = open(os.path.join(save_dir,"seeder_leecher_stats.dat"),"w")
    print range(0, int(end-start), 20)
    for time in range(0, int(end-start), 20):
        seeder = 0
        leecher = 0
        for (peer_stats, peer_infos) in client_info:
            try:
                if time > float(peer_stats['leeching_start']) and time + start < float(peer_stats['leeching_finished']):
                    leecher += 1
            except:
                pass
            try:
                if time > float(peer_stats['seeding_start']) and time + start < float(peer_stats['seeding_finished']):
                    seeder += 1
            except:
                pass
        
        seeder_leecher_file.write("%f %d %d\n" % (time, seeder, leecher))
        
                
    
    
def get_hostname(ip):
    host = socket.gethostbyaddr(ip)
    split = host[0].partition('.')
    s = None
    if split[2] == '':
        s = split[0]
    else:
        s = split[2]
    return s   
                    
def main(options):
    read_client_stats(options.directory)
    (stats, start, end) = process_client_info(options.save_dir)
    #write_seeder_leecher(start, end, options.save_dir)
    write_stats(options.save_dir, stats)         
    
                    
if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d", "--directory", 
                      action="store", dest="directory")
    parser.add_option("-s", "--save_dir", 
                      action="store", dest="save_dir", default=None)
    
    (options, args) = parser.parse_args()
    
    main(options)
    