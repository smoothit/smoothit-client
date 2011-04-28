from time import time
import sys
import os
from threading import Lock
from BaseLib.Core.simpledefs import *
from SisClient.Testbed.Utils.utils import *

class Statistic:
    ''' This class processes the reports sent by the clients and generates statistics.
    '''
    
    def __init__(self):
        self.clean()
    
    def clean(self):
        self.clients = dict()
        self.plots = dict()
        self.file_statistics = dict()
        self.basedir = "stats"
        self.start_time = None
        FileUtils.create_directory(self.basedir, removeOld=True)
    
    def add_report(self, report):
        
        if self.start_time == None:
            self.start_time = report['timestamp']
        
        id = report['id']
        filename = report['filename']
        
        if not self.clients.has_key(id):
            self.clients[id] = {'files': dict()}  
        client = self.clients[id]
        
        if not client['files'].has_key(filename):
            client['files'][filename] = self.new_file(filename, id)
        file = client['files'][filename]
        
        self.set_timemarks(report, file)
            
        file['handler'].write('%f %f %f\n' % (report['timestamp'] - self.start_time, report['down_rate'], report['up_rate']))
        file['handler'].flush()
        
        file['up_total'] = report['up_total']
        file['down_total'] = report['down_total']
        file['complete'] = report['progress']
    
    def set_timemarks(self, report, file):
        if file['leeching_start'] == None and int(report['status']) == DLSTATUS_DOWNLOADING:
            file['leeching_start'] = report['timestamp'] -self.start_time
        if file['seeding_start'] == None and int(report['status']) == DLSTATUS_SEEDING:
            file['seeding_start'] = report['timestamp'] -self.start_time
        if int(report['status']) == DLSTATUS_DOWNLOADING:
            file['leeching_finished'] = report['timestamp'] -self.start_time
        if int(report['status']) == DLSTATUS_SEEDING:
            file['seeding_finished'] = report['timestamp'] -self.start_time
        
    
    def write_all(self):
        self.create_plots()
        self.write_plots()
        self.write_statistic_files()
        self.write_file_statistics()
        
    
    def create_plots(self):
        for (id, clientvalues) in sorted(self.clients.items()):
            clientname = "client %d" % id
            for filename, filevalues in clientvalues['files'].items():
                filevalues['handler'].close()
                if not self.plots.has_key(filename):
                    self.plots[filename] = self.new_fileplot(filename)
                plot = self.plots[filename]
                
                plot['down'].addPlot(self.get_filename(filename, id),
                                     using="1:2", title=clientname, style="lines", 
                                     other="smooth csplines")
                plot['up'].addPlot(self.get_filename(filename, id),
                                  using="1:3", title=clientname, style="lines", 
                                  other="smooth csplines")
    
    def write_plots(self):
        try:
            for entry in self.plots.values():
                entry['up'].commitPlot()
                entry['down'].commitPlot()
        except:
            print >> sys.stderr, 'couldn\'t create plots.' 
        
    def write_statistic_files(self):
        for (id, values) in self.clients.items():
            name = "client %d" % id
            path = os.path.join(self.basedir,'%s_stats.txt' % name)
            handler = open(path, 'w')
            handler.write('%s\n' % name)
            down_total = 0.0
            up_total = 0.0
            
            for (fname,info) in values['files'].items():
                handler.write('\nfilename: %s\n' % fname)
                handler.write('download: %f MB\n' % (info['down_total'] / 1024.0))
                handler.write('upload: %f MB\n' % (info['up_total'] / 1024.0))
                
                down_total += (info['down_total'] / 1024.0)
                up_total += (info['up_total'] / 1024.0)
                
                try:
                    dl_time = info['leeching_finished'] - info['leeching_start']
                except:
                    dl_time = 0
                
                dl_start = info['leeching_start']
                dl_end = info['leeching_finished']
                
                try:
                    seeding_time = info['seeding_finished'] - info['seeding_start']
                except:
                    seeding_time = 0

                seeding_start = info['seeding_start']
                seeding_end = info['seeding_finished']
                
                handler.write('dl_time: %f s\n' % dl_time)
                handler.write('seeding_time: %f s\n' % seeding_time)
                handler.write('leeching: %s - %s\n' % (dl_start, dl_end))
                handler.write('seeding: %s - %s\n' % (seeding_start, seeding_end))
                handler.write('complete: %d%%' % info['complete'])
                
                if not self.file_statistics.has_key(fname):
                    self.file_statistics[fname] = self.new_file_statistic()
                
                fstat = self.file_statistics[fname]
                if info['complete'] == 100:
                    if dl_time > 0:
                        fstat['finished'] += 1
                        fstat['dl_times'].append(dl_time)  
                else:
                    fstat['unfinished'] += 1
            
            handler.write('\ndown_total: %f MB\n' % down_total)
            handler.write('up_total: %f MB\n' % up_total)
            handler.close()
            
    def write_file_statistics(self):
        for (fname, info) in self.file_statistics.items():
            file = os.path.join(self.basedir, fname+"_stats.txt")
            handler = open(file, "w")
            handler.write('finished: %d\n' % info['finished'])
            handler.write('unfinished: %d\n' % info['unfinished'])
            
            if len(info['dl_times']) > 0:
                total_dl_time = 0.0
                    
                for dl_time in info['dl_times']:
                    total_dl_time += dl_time
                handler.write('average download time: %fs' % (total_dl_time/len(info['dl_times'])))
                
                for dl_time in info['dl_times']:
                    handler.write("\n%f" % dl_time)
        
            handler.close()
        
    def get_total(self, dir, timeline):
        total = []
        for n in range(0, len(timeline['client'][dir])):
            total.append(timeline['client'][dir][n]+timeline['cache'][dir][n])
        return total
    
    def new_file(self, filename, id):
        handler = open(self.get_filepath(filename, id), 'w')
        return {'leeching_start': None, 'leeching_finished': None,
                'seeding_start': None, 'seeding_finished': None, 
                'down_total': 0, 'up_total': 0, 'complete': 0, 'handler': handler}
    
    def new_fileplot(self, filename):
        fileplot = dict()
        fileplot['down'] = self.new_plot(filename, 'down')
        fileplot['up'] = self.new_plot(filename, 'up')
        return fileplot
        
    def new_plot(self, filename, dir):
        name = filename+'_'+dir
        return Plotter(self.basedir, name, name+'.plt', 'eps', 'time(s)', 'rate(kb/s)', xrange ="[0:]", yrange="[0:]")
    
    def get_filename(self, file, id):
        return file + '_client'+ str(id) + '.dat' 
    
    def get_filepath(self, file, id):
        return os.path.join(self.basedir, self.get_filename(file, id)) 
    
    def set_basedir(self, basedir):
        self.basedir = basedir
        
    def new_file_statistic(self):
        return {'finished': 0, 'unfinished': 0,  'dl_times': []}
        
class Plotter(object):
    def __init__(self, baseDir, outputFile, plotFile, type, xlabel=None, ylabel=None, 
                 xrange=None, yrange=None):
        self.plotFile = os.path.join(baseDir,plotFile)
        self.baseDir = baseDir
        outFile = outputFile
        
        self.out = open(self.plotFile, 'w')
        terminal_type = type
        if terminal_type == "png":
            outFile +=".png"
        elif terminal_type == "eps":
            terminal_type = 'postscript color eps'
            outFile +=".eps"
        else:
            raise Exception("unsupported terminal type: "+terminal_type)
        self.out.write("set terminal "+terminal_type+"\n")
        #TODO: png vs. eps
        self.out.write("set output '"+outFile+"'\n")
        if xlabel: self.out.write("set xlabel '"+xlabel+"'\n")
        if ylabel: self.out.write("set ylabel '"+ylabel+"'\n")
        if xrange: self.out.write("set xrange "+xrange+"\n")# ignore server, that has node id -1
        if yrange: self.out.write("set yrange "+yrange+"\n")# for better comparison between setups

        self.plotCounter = 0

    def addPlot(self, inFile, using="1:2", title=None, style="points", other=None):
        if self.plotCounter is 0: 
            self.out.write("plot ")
        else: 
            self.out.write(",\\\n")# means just ",\" and newline
        self.out.write("'"+inFile+"' u "+using+" with "+style)
        if title:
            self.out.write(" t '"+title+"'")
        if other:
            self.out.write(" "+other)        
        self.plotCounter+=1

    def commitPlot(self):
        """        
        """
        #TODO: should we use relative path instead?
                          
        self.out.write("\n")# terminate plot line
        self.out.close
        self.out=None#strange bug! otherwise it will not be written yet!!!
        
        self.plot(self.plotFile)
    
    # invoke gnuplot with the given file
    def plot(self, plotfile):
            
        print "run "+plotfile
        
        before = os.getcwd()
        
        os.chdir(os.path.dirname(plotfile))
        try:
            cmd = 'gnuplot '+os.path.basename(plotfile)
            r = os.system(cmd)
            if r != 0:
                print 'gnuplot failed: '+plotfile
        finally:
            os.chdir(before)

        