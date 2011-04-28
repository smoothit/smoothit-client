import cgi, time, zlib
import select
import sys
import pickle
import optparse

from analyzer import ReportAnalyzer
from SisClient.Testbed.Utils.statistic import Statistic
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

__author__ = "Markus Guenther"

analyzer = ReportAnalyzer()
statistic = Statistic()

class ReportHandler(BaseHTTPRequestHandler):
    '''
    This class is a very minimalistic handler that allows POST requests to
    the base directory of a webserver instance. The POST data should contain
    reports from clients. Currently, those reports are processed and written
    to a log file.
    '''
    def do_HEAD(self):
        '''
        The HEAD command is not implemented and therefore prohibited. The
        handler reflects this by sending back the HTTP status code 501.
        '''
        self.send_error(501)
        
    def do_GET(self):
        '''
        The GET command is not implemented and therefore prohibited. The
        handler reflects this by sending back the HTTP status code 501.
        '''
        self.send_error(501)
    
    def do_POST(self):
        '''
        The POST command is used to pass reports to the webserver, which 
        processed the received data further. If the addressed path on the
        webserver is not the root directory, the webserver responds with
        the HTTP status code 403.
        '''
        global analyzer
        global statistic
        
        if self.path is not "/":
            self.send_error(403)
            return
        
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        length = int(self.headers.getheader('content-length'))
        report = pickle.load(self.rfile)
        
        # dispatch the report to the analyzer
        analyzer.put_report(report)
        statistic.add_report(report)
        
        # throw away additional data [see bug #427345]
        while select.select([self.rfile._sock], [], [], 0)[0]:
            if not self.rfile._sock.recv(1):
                break
            
        self.send_response(200)
        
if __name__ == "__main__":
    parser = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options]")
    
    parser.add_option("-p", "--port",
                      action="store", dest="server_port", default=8888,
                      help="Specifies the server port. Defaults to 8888.")
    parser.add_option("-u", "--url",
                      action="store", dest="server_url", default="localhost",
                      help="Specifies the server address. Defaults to localhost.")
    
    (options, args) = parser.parse_args()
    
    try:
        server = HTTPServer((options.server_url, options.server_port), ReportHandler)
        print "Server running at: %s:%s" % (options.server_url, options.server_port)
        while True:
            server.handle_request()
    except KeyboardInterrupt:
        print "Closing server socket."
        server.socket.close()
