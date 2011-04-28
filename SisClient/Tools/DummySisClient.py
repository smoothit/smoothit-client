#!/usr/bin/env python

import sys,time
from ZSI.client import NamedParamBinding as NPBinding
from ZSI.wstools import WSDLTools
from SisClient.RankingPolicy.WebService.ClientService_client import *
from SisClient.RankingPolicy.WebService.ClientService_types import *
import unittest
import traceback
import optparse

class requestEntry:
    def __init__(self, ipAddress, extentions):
        self._ipAddress = ipAddress
        self._extentions = extentions
        
class request:
    def __init__(self, entries, extentions):
        self._entries = entries
        self._extentions = extentions

def extract(res):    
    # return only ips with pref > 0
    # What fields do exist here?
    #print dir(res)
    
    ips = dict()
    for responseEntry in res._response._entries:
        #print responseEntry._ipAddress, ' ', responseEntry._preference
        #if responseEntry._preference > 0:
        ips[responseEntry._ipAddress] = responseEntry._preference
    return ips   

class DummySisClient:

    def __init__(self, sis_url, peer_list_file, verbose):
        self.sis_url = sis_url
        self.verbose = verbose
        
        if (verbose): print "USE peer list = %s" % peer_list_file
        if peer_list_file:
            self.peer_list = []
            f = open(peer_list_file, 'r')
            for line in f:
                ip = line.replace('\n','')
                self.peer_list.append(ip)
        else:
            self.peer_list = ['192.168.2.1', '192.168.2.2', '192.168.2.3', "193.99.144.85","130.83.198.177", "130.83.139.168"]

    def populate(self, req):    
        extentions = ['This is an extension', 'And here is another one']
        requestEntries = []
        req._arg0 = request(requestEntries, extentions)
           
        #insert entries
        for ip in self.peer_list:
            reqEntry = requestEntry(ip, ['extension of ip'])
            requestEntries.append(reqEntry)        
    
    def performRequest(self, simple=False):
        if(self.verbose): print "USE  sis_url = %s" % self.sis_url
        
        loc = ClientServiceLocator()
        self.srv = loc.getClientServicePort(self.sis_url)
        
        #build request
        if(simple):
            req = SisClientPort_getSimpleRankedPeerList()
        else:
            req = SisClientPort_getRankedPeerList()
            
        #print "Send list:",self.peer_list
        if(self.verbose): print "Send ip list %s:" % self.peer_list
        self.populate(req)
        sent_time = time.time()
        if(simple):
            res = self.srv.getSimpleRankedPeerList(req)
        else:
            res = self.srv.getRankedPeerList(req)
        received_time = time.time()
        ips = extract(res)
        assert len(ips)==len(self.peer_list), "Expected %s but got %s" % (str(self.peer_list), str(ips))
        if (self.verbose): print "Received ratings:",ips
        return (sent_time, received_time, (received_time - sent_time))
        #assert len(ips)==1
    
# MAIN STARTS HERE
if __name__ == '__main__':
    # TODO: add options: verbose, sis_url, file list, simple
    
    parser = optparse.OptionParser(usage="USAGE: " + sys.argv[0] + " [options]",
                               description="This script will send an ip list ranking request to SIS server.", version=sys.argv[0] + " 0.1")
        
    parser.add_option("-u", "--sis_url",
                      action="store", dest="sis_url", default="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl",
                      help="URL of the SIS server (client protocol endpoint).")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Verbose mode (print details about IPs and SIS rankings).")
    parser.add_option("-f", "--ip_list_file",
                      action="store", dest="peer_list_file", default=None,
                      help="File with the list of IPs to be sent to the SIS server (one IP per line)")
    parser.add_option("-s", "--simple_ranking",
                      action="store_true", dest="simple", default=False,
                      help="Use simple ranking (allow for very lightweight tests).")
    
    (options, args) = parser.parse_args()
    
    if len(args)>0:
        parser.print_help()
        parser.error("Two many arguments: "+str(args))
        sys.exit(-1)
        
    try:
        client = DummySisClient(options.sis_url, options.peer_list_file, options.verbose)
        #client = DummySisClient()
        result = client.performRequest(options.simple)
        
        print "SIS_CONNECTED sent %f, received %f, duration %f" % result
    except:
        traceback.print_exc()
        print "SIS_Failure"
    
#url = 'http://127.0.0.1:8080/Test'
#
## just use the path to the wsdl of your choice
#reader = WSDLTools.WSDLReader();
#wsdlfile = reader.loadFromURL(url + '?WSDL');
#print "Services: ----------------"
#print wsdlfile.services
