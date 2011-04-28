# This Python file uses the following encoding: utf-8
import sys,time
import logging

from ZSI.client import NamedParamBinding as NPBinding
from ZSI.wstools import WSDLTools
from SisClient.RankingPolicy.WebService import ClientService_client as WS
from traceback import print_exc
import SisClient.RankingPolicy.RankingPolicy as RankingPolicy

__author__ = "Sebastian Schmidt, Markus Günther"

# ranking to use if SIS communication fails
DEFAULT_RANKING = 0

class requestEntry:
    def __init__(self, ipAddress, extentions):
        self._ipAddress = ipAddress
        self._extentions = extentions
        
class request:
    def __init__(self, entries, extentions):
        self._entries = entries
        self._extentions = extentions

class Communicator(RankingPolicy.RankingPolicy):
    def __init__(self, sis_url=None, simple=False, max_time_in_cache=60):
        self._logger = logging.getLogger("Communicator")
        
        # defines the maximum amount of time (in seconds) a cached ip address
        # resides in the cache. after MAX_TIME_IN_CACHE seconds the ip address
        # will be deleted from the ip cache.
        self.MAX_TIME_IN_CACHE = max_time_in_cache
        
        self.ipcache = {}
        self.simple=simple
        loc = WS.ClientServiceLocator()
        self.request_number = 0# count requests
        if sis_url is None:
            self._logger.warn("NO SIS URL SPECIFIED")
            self.srv = loc.getClientServicePort()
        else:
            self._logger.info("USE SIS URL: "+str(sis_url))
            self.srv = loc.getClientServicePort(sis_url)
            
    def _get_endpoint(self, simple):
        '''Returns the interface to the communication endpoint in dependance
           of the simple or default ranking.
        '''
        if simple:
            return WS.SisClientPort_getSimpleRankedPeerList(), \
                   ["getSimpleRankedPeerList_extension"]
        else:
            return WS.SisClientPort_getRankedPeerList(), \
                   ["getRankedPeerList_extension"]
                   
    def _filter_iplist(self, iplist):
        '''Filters a given list of IP addresses into a list of those IP
           addresses that were requested before and are still in the IP cache 
           and a second list which contains those IP addresses that are not
           stored in the cache.
           
           Returns the tuple (nonCachedIps, cachedIps)
        '''
        cachedIps = [ip for ip in iplist if ip in self.ipcache.keys()]
        nonCachedIps = [ip for ip in iplist if ip not in cachedIps]
        
        return nonCachedIps, cachedIps
    
    def _build_request_entries(self, listOfIps):
        '''Build a list of request entries for a given list of IP addresses.
           Checks if those addresses are stored in the IP cache before adding
           a request entry to the resulting list.
           
           Returns a list of request entries.
        '''
        # TODO: redundant check for caching inside, the ips are already cached
        requests = []
        j = 0
        for ip in listOfIps:
            if ip not in self.ipcache.keys():
                requests.append(requestEntry(ip, [str(j)]))
                j += 1
                
        return requests
    
    def _get_result(self, simple, endpoint):
        '''Retrieves the result, depending on the ranking method (simple or not).
        '''
        if simple:
            return self.srv.getSimpleRankedPeerList(endpoint)
        else:
            return self.srv.getRankedPeerList(endpoint)
        
    def _map_ip_to_preference(self, result):
        '''Consumes a result object and builds a dictionary of IPs (key) with
           their preferences as values.
        '''
        chosenIps = dict([(responseEntry._ipAddress, responseEntry._preference)
                          for responseEntry in result._response._entries])
        return chosenIps
    
    def _cache_ip_addresses(self, result):
        ts = time.time()
        for responseEntry in result._response._entries:
            self.ipcache[responseEntry._ipAddress] = {
                    'timestamp'    :   ts,
                    'preference'   :   responseEntry._preference
            }
    
    def _get_pref_for_cached_ips(self, cachedIps):
        '''Returns a dictionary containing preferences for all cached IP
           addresses.
        '''
        return dict([(ip, self.ipcache[ip]["preference"]) for ip in cachedIps])
    
    def _update_ipcache(self):
        '''Checks for "old" IP addresses in the cache and removes them.
        '''
        ts = time.time()
        for ip in self.ipcache.keys():
            timeInCache = ts - self.ipcache[ip]['timestamp']
            if timeInCache > self.MAX_TIME_IN_CACHE:
                del self.ipcache[ip]

    def _get_sum(self, x, y):
        '''
        This method is used just to test the SIS availablility.
        It simply returns the sum of the two arguments.
        '''
        req = WS.SisClientPort_add()
        req._arg0 = 9
        req._arg1 = 10
        return self.srv.add(req)._sum

    def getRankedPeers(self, iplist):
        '''Returns a dictionary of IP addresses (keys) with their preferences
           as values.
        '''
        # see if there are old ip addresses in the cache and delete them
        self._update_ipcache()
        # remove duplicates
        iplist = list(set(iplist))
        # filter non-cached and cached ips into disjoint lists
        nonCachedIps, cachedIps = self._filter_iplist(iplist)
        prefForCachedIps = self._get_pref_for_cached_ips(cachedIps)
        
        self._logger.debug("Cached IPs: %s" % str(cachedIps))
        self._logger.debug("Non-cached IPs: %s" % str(nonCachedIps))
        
        # if the length of the nonCachedIp list is zero, just return the
        # cached preferences
        if len(nonCachedIps) is 0:
            self._logger.info("Using only cached IPs: %s" % str(prefForCachedIps))
            return prefForCachedIps

        # in order to get preference values for the non-cached ips, we need
        # to build a list of request entries for the SIS server 
        ipRequests = self._build_request_entries(nonCachedIps)
        
        endpoint, extensions = self._get_endpoint(self.simple)
        endpoint._arg0 = request(ipRequests, extensions)

        try:
            self.request_number+=1
            self._logger.info("Connect to SIS, send : " + str(nonCachedIps))
            result = self._get_result(self.simple, endpoint)
            self._cache_ip_addresses(result)
            chosenIps = self._map_ip_to_preference(result)
            self._logger.info("Connection to SIS succeed, received : "+ str(chosenIps))
        except:
            self._logger.error("FAILED TO CONNECT TO SIS at %s" % self.srv.url, exc_info=True)
            #raise RuntimeError("SIS communication failed. stop")
            chosenIps = {}
            for ip in nonCachedIps:
                chosenIps[ip] = DEFAULT_RANKING
            self._logger.warn("Use default rankings for %s" % str(chosenIps))
        
        # combine the two ip dicts
        combinedIps = dict(chosenIps)
        combinedIps.update(prefForCachedIps)
        
        return combinedIps