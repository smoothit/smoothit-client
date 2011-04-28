# Written by Sebastian Schmidt (TUD)
# see LICENSE.txt for license information
from SisClient.RankingPolicy.RankingPolicy import RankingPolicy
import logging
import random
import socket

_instance = None

def getInstance():
    global _instance
    if _instance is None:
        _instance = NoFiltering()
    #_logger.debug("Biased neighbor filtering "+str(_instance))
    return _instance

def ns_instance():
    return _instance

def createMechanism(mode, rankingSource = None, exclude_below = None, locality_pref=None):
    '''
    Select appropriate implementation according to the mode value.
    Config is not required for the "none" mode.
    Communicator is required for "simple" and "regular" modes. 
    '''
    assert rankingSource is None or isinstance(rankingSource, RankingPolicy), rankingSource
    global _instance
    if mode=='none' or mode == None:
        _instance = NoFiltering()                
    elif mode=='enable':
        _instance = SISFiltering(locality_pref, rankingSource, exclude_below)
    elif mode=='cache_local':
        _instance = CacheFiltering()
    elif mode=='cache_port':
        _instance = CachePortFiltering()
    else:
        raise Exception("Unsupported neighbor selection mode: "+mode)
    return _instance

class NeighborSelection:
    '''
    Abstract class which provides a method to select peers in dependence of the used mode. The concrete 
    implementation is chosen in dependence of the given booleans.
    The selection can be used for the filtering of peer-IDs returned by the tracker.
    '''
    
    def __init__(self):
        self._logger = logging.getLogger("NeighborSelection")
    
    def selectAsNeighbors(self, ipPortList, number=-1):
        '''
        Returns a reorded list of the given IP-Port-Tupels due to the concrete implementation.
        If number is given, the result contains at most number elements, else it contains all peers.
        '''          
        raise NotImplementedError()
    
    def acceptAsNeighbor(self, ipPort):
        '''
        Returns a boolean due to the concrete implementation.
        '''
        raise NotImplementedError()
    
    def _fillUp(self, all, number, locality_pref = 1.0):
        '''
        Returns a list with at most "number" entries while peeking local_pref best.
        '''
        self._logger.debug("Locality pref is %f" % locality_pref)
        
        if number == -1: number = len(all)
        else: number = min(number, len(all))

        self._logger.debug("HighRanks: %s \nnumber %d" % (str(all), number))
        self._logger.debug("high_ranks %d" % (len(all)))

        #1. pick best according to the locality pref
        local_nr = int(number*locality_pref)
        other_nr = number - local_nr
        self._logger.debug("local_nr=%d other_nr=%d" % (local_nr, other_nr))                
        result = all[0:local_nr]
        self._logger.debug("Preferred: %s" % str(result)) 
        others = all[local_nr:]
        random.shuffle(others)
        result.extend(others[0:other_nr])
        assert len(result)==number, "result has size %d instead of expected %d" % (len(result), number)
        self._logger.info("Result: %s" % str(result))    
        
        return result

class NoFiltering(NeighborSelection):
    '''
    No filtering of peers takes place.
    '''
    
    def __init__(self):
        NeighborSelection.__init__(self)
        self._logger.info("Don't use biased neighbor filtering")
    
    # no filtering before adding new IPs of other leechers and seeders
    def selectAsNeighbors(self, ipPortList, number=-1):
        if number < 0:
            number = len(ipPortList)
        result = ipPortList[0:number]
        self._logger.debug(" NOT USING ANY FILTERING")
        self._logger.debug(" ADDING - " + str(result))
        return result
    
    # accept every peer
    def acceptAsNeighbor(self, ipPort):
        self._logger.debug(" NOT USING ANY FILTERING")
        self._logger.debug(" ACCEPTING - " + str(ipPort))
        return True

class SISFiltering(NeighborSelection):
    '''
    Filter candidate peers based on the rankings provided by the given rankingSource.
    '''
    
    def __init__(self, locality_pref, rankingSource, exclude_below = None):
        '''
        rankingSource is a generic source to map (ip, port) tuples to ranks (>=0),
        config provides general configuration parameters, while
        exclude_below will enforce to ignore all peers with rankings below this value.
         
        '''
        NeighborSelection.__init__(self)
        assert rankingSource
        self.locality_pref = locality_pref
        self.rankingSource = rankingSource        
        self.exclude_below = exclude_below or 0 # default is not to exclude anybody!
        self._logger.info("USE REGULAR FILTERING with rankingSource=%s, exclude_below=%f" % (rankingSource, self.exclude_below))
        
    # remote filtering before adding new IPs of other leechers and seeders
    def selectAsNeighbors(self, ipPortList, number=-1):
        #print "SELECT AS NEIGHBORS FOR", ipPortList
        self._logger.debug(" USING REMOTE FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPortList))
        ipList = []
        for (ip, port) in ipPortList:
            ipList.append(ip)
        rankedIPs = self.rankingSource.getRankedPeers(ipList)
        
        #print "ranked: ", rankedIPs
        if rankedIPs is None:
            # Failed to connect to SIS
            self._logger.warn(" SIS COMMUNICATION FAILED - PROCEED IN NORMAL MODE")
            return ipPortList
        filtered = []
        #lowRanking = []
        for (ip, port) in ipPortList:
            if int(rankedIPs[ip]) >= self.exclude_below:
                filtered.append((ip, port))
            else:
                self._logger.debug("Skip remote ip %s because its rating is too low!" % ip)
            # completely ignore low rankings
            #else:
            #    lowRanking.append((ip, port))
            
        #print "filtered=", filtered
        # now set according to the filtering!
        my_key = lambda x : rankedIPs[x[0]] # ip part ranked by the mechanism
        filtered.sort(key=my_key, reverse = True)
        #print "sorted=", filtered
        result = self._fillUp(filtered, number, locality_pref=self.locality_pref)
        self._logger.debug(" Ranked IPs are: - " + str(rankedIPs))
        self._logger.debug(" ADDING - " + str(result))
        return result
    
    # decide remotely if the peer with given ip should be accepted
    # peers with preference larger than one are accepted
    def acceptAsNeighbor(self, ipPort):
        self._logger.debug(" USING REMOTE FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPort))
        (ip, port) = ipPort
        rankedIPs = self.rankingSource.getRankedPeers([ip])
        if rankedIPs is None:
            # Failed to connect to SIS
            self._logger.debug(" Ranking FAILED - accept unranked peer "+str(ipPort))
            return True  
        self._logger.debug(" SIS-RESPONSE - " + str(rankedIPs))
        if int(rankedIPs[ip]) > 0:
            self._logger.debug(" ACCEPTED - " + str(ipPort))
            return True
        else:
            return False
        
class CacheFiltering(NeighborSelection):
    ''' This class filters the iplist by comparing hostnames.
        Works for glab but not for local tests.
    '''
    
    def __init__(self):
        NeighborSelection.__init__(self)
        self.cache_hostname = None
        self.allowed_ips = []
        self._logger.debug("USE CACHE-FILTERING")
    
    def selectAsNeighbors(self, ipPortList, number=-1):
        result = []
        for (ip, port) in ipPortList:
            if self.is_local(ip):
                result.append((ip,port))
        self._logger.debug(" USING CACHE FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPortList))
        self._logger.debug(" ADDING - " + str(result))
        return result
    

    def acceptAsNeighbor(self, ipPort):
        self._logger.debug(" USING CACHE FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPort))
        (ip, port) = ipPort
        return (self.is_local(ip) or self.allowed_ips.__contains__(ipPort))
    
    def is_local(self, ip):
        host = socket.gethostbyaddr(ip)
        split = host[0].partition('.')
        s = None
        if split[2] == '':
            s = split[0]
        else:
            s = split[2]
        return self.cache_hostname.endswith(s)
    
    def set_cache_hostname(self, hostname):
        self.cache_hostname = hostname[0]
    
    def add_allowed_ip(self, ipPort):
        self.allowed_ips.append(ipPort)
        
class CachePortFiltering(NeighborSelection):
    ''' This class is used to determine the locality of a peer in local tests.
    '''
    
    def __init__(self):
        NeighborSelection.__init__(self)
        self.allowed_ports= (10011, 10012, 10014, 10015, 10001)
        self._logger.info("USE CACHE-PORT-FILTERING with allowed ports %s" % self.allowed_ports)
    
    def selectAsNeighbors(self, ipPortList, number=-1):
        result = []
        for (ip, port) in ipPortList:
            if self.allowed_ports.__contains__(port):
                result.append((ip,port))
        self._logger.debug(" USING CACHE-PORT FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPortList))
        self._logger.debug(" ADDING - " + str(result))
        return result
    

    def acceptAsNeighbor(self, ipPort):
        self._logger.debug(" USING CACHE-PORT FILTERING")
        self._logger.debug(" REQUESTED - " + str(ipPort))
        (ip, port) = ipPort
        return self.allowed_ports.__contains__(port)
    
