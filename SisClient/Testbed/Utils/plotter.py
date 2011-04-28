import platform
import sys
import os
#import config

class Plotter(object):
    def __init__(self, baseDir, inputFile, outputFile, plotFile, xlabel=None, ylabel=None, 
                 xrange=None, yrange=None):
        self.inFile = inputFile
        self.plotFile = os.path.join(baseDir,plotFile)
        outFile = outputFile
        
        self.out = open(self.plotFile, 'w')
        #terminal_type = config.config.get('gnuplot', 'output_file_type')
        terminal_type = "png"
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

    def addPlot(self, using="1:2", title=None, style="points", other=None):
        if self.plotCounter is 0: 
            self.out.write("plot ")
        else: 
            self.out.write(",\\\n")# means just ",\" and newline
        self.out.write("'"+self.inFile+"' u "+using+" with "+style)
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
                
#        if config.defaults["windows"]:
#            gnuplot = "wgnuplot"
#        else:
#            gnuplot = "gnuplot"
        gnuplot = "gnuplot"   
        print "run "+plotfile
        
        before = os.getcwd()
        os.chdir(os.path.dirname(plotfile))
        try:
            cmd = gnuplot+' '+os.path.basename(plotfile)
            r = os.system(cmd)
            #print os.system("gnuplot foo.bar")
            if r != 0:
                print 'gnuplot failed: '+plotfile
        finally:
            os.chdir(before)
