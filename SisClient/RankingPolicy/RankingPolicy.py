import sys
import socket
import logging

from SisClient.Utils import ipaddr_utils

__author__ = "Konstantin Pussep"

def selectRankingSource(source, conf=None):
    
    ''' Select an appropriate ranking source depending on the configuration.
    
        Params:
            source    -- specifies the ranking policy to be used
                         admissible values are: none, samehost, odd_even, sis, sis_simple, ip_pre
            conf      -- (optional) configuration instance (from cache or client)
    '''
    if source == 'samehost':
        ranking = SameHostPolicy()
    elif source == 'odd_even':
        ranking = OddEvenPolicy()
    elif source == 'geoip':
        ranking = GeoIPPolicy()
    elif source == 'sis':
        import Communicator
        assert conf != None
        assert conf.get_sis_client_endpoint() != None
        assert conf.get_rating_cache_interval() != None
        ranking = Communicator.Communicator(conf.get_sis_client_endpoint(), simple=False,
                                            max_time_in_cache=conf.get_rating_cache_interval())
    elif source == 'sis_simple':
        import Communicator
        assert conf != None
        assert conf.get_sis_client_endpoint() != None
        assert conf.get_rating_cache_interval() != None
        ranking = Communicator.Communicator(conf.get_sis_client_endpoint(), simple=True,
                                            max_time_in_cache=conf.get_rating_cache_interval())
    elif source == 'ip_pre':
        assert conf != None
        assert conf.get_ip_prefixes() != None
        ranking = SameIPPrefixPolicy(conf.get_ip_prefixes())
    elif source in (None, 'none', 'None'):
        ranking = DummyPolicy()
    else:
        raise Exception("Unsupported ranking type: " + source)
    return ranking

class RankingPolicy:
    '''
    Basic ranking interface.
    '''
    
    def __init__(self):
        self._logger = logging.getLogger("RankingPolicy")
    
    def getRankedPeers(self, iplist):
        ''' Return a ranked dictionary, containing all ips from the ip list together
        with a non-negative integer ranking as a dictionary -{"IP":"value"}.
        '''
        raise NotImplementedError("Must be implemented by subsclasses")

class DummyPolicy(RankingPolicy):
    ''' Rank all peers with the same value.
    '''
    def __init__(self):
        RankingPolicy.__init__(self)
    
    def getRankedPeers(self, iplist):
        res = dict()
        for ip in iplist:
            res[ip] = 100
        return res


class SameHostPolicy(RankingPolicy):
    ''' Rank the same host with a positive value, all other with 0.
    '''

    def __init__(self, own_ip=None):
        RankingPolicy.__init__(self)
        if own_ip == None:
            sys_name = socket.gethostname()
            # IP adress
            self.ip_addr = socket.gethostbyname(sys_name)
        else:
            self.ip_addr = own_ip

    def getRankedPeers(self, iplist):
        #return RankingPolicy.getRankedPeers(self, iplist)
        res = dict()
        for ip in iplist:
            if ip in ("127.0.0.1",self.ip_addr):
                res[ip] = 100
            else:
                res[ip] = 0
        return res
    
# # TODO: check if pygeoip is installed!
geo_ip_found = False
try:
    import pygeoip
    try:
        path = "resources/GeoLiteCity.dat"
        gi_city = pygeoip.GeoIP(path)
        #gi_isp = pygeoip.GeoIP("resources/GeoIPISP.dat")
        geo_ip_found = True
    except:
        print >>sys.stderr, "Missing the required geoip database for GeoIPPolicy (if desired) %s, you can find it here: http://geolite.maxmind.com/download/geoip/database/" % path
except:
    print >>sys.stderr, "pygeoip is not installed! GeoIPPolicy cannot be used...(see http://code.google.com/p/pygeoip/ to download it)"
    
class GeoIPPolicy(SameHostPolicy):
    ''' Rank the same host with a positive value, all other with 0.
    '''

    def __init__(self, own_ip=None):
        SameHostPolicy.__init__(self, own_ip)
        if not geo_ip_found:
            raise Exception("Geo ip is not installed!")
        self.own_ip_info = gi_city.record_by_addr(self.ip_addr)
        self._logger.info("ip info %s for ip addr %s " % (self.own_ip_info, self.ip_addr))
        #print "own info: ", self.own_ip_info

    def getRankedPeers(self, iplist):
        if self.own_ip_info is None:
            # Probably we got a local IP address before, so try now to get the right one from the session (created AFTER this policy!)
            from BaseLib.Core.Session import Session
            self.ip_addr = Session.get_instance().get_external_ip()
            self.own_ip_info = gi_city.record_by_addr(self.ip_addr)
            self._logger.info("ip info %s for ip addr %s " % (self.own_ip_info, self.ip_addr))
        #return RankingPolicy.getRankedPeers(self, iplist)
        res = dict()
        for ip in iplist:
            other = gi_city.record_by_addr(ip)
            if self._compareFiled(self.own_ip_info, other, 'city'):
                res[ip] = 1000
            elif self._compareFiled(self.own_ip_info, other, 'region') \
            or self._compareFiled(self.own_ip_info, other, 'region_name'):
                res[ip] = 500
            elif self._compareFiled(self.own_ip_info, other, 'country_name'):
                res[ip] = 250
            else:
                res[ip] = 0
         
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Ranked iplist %s" % str(res)) 
            
        return res
    
    def _compareFiled(self, info1, info2, field_name):
        if info1 and info2 and info1.has_key(field_name) and info2.has_key(field_name):
            value1 = info1[field_name]
            value2 = info2[field_name]
            if value1 and value2:
                return value1==value2
        return False
    
class OddEvenPolicy(RankingPolicy):
    ''' Distinguish odd (-->0) and even (--> larger than 0) IP addresses.
    '''
    def __init__(self):
        RankingPolicy.__init__(self)
    
    def getRankedPeers(self, iplist):
        res = dict()
        for ip in iplist:
            # can switch between odd and even rankings here, why not offer both? local_odd, local_even, local_strict
            if int(ip.replace(".","")) % 2 == 0 :
                res[ip] = 100
            else:
                res[ip] = 0
        return res
    
        # MOVED to utils
    def compare_odd_even(self, c1, c2):
        '''Compare two connections, the ones with even IP addresses are considered "more local" i.e. smaller..'''
        ip1_even = (int(c1.get_ip().replace(".","")) % 2 ==0) 
        ip2_even = (int(c2.get_ip().replace(".","")) % 2 == 0)
        if ip1_even == ip2_even: return 0 # equal
        elif ip1_even: return -1# only c1 is "close"
        else: return 1# only c2 is close

        # filter locally
    def selectConnections(self, connections, number=-1):
        result = sorted(connections, self.compare_odd_even)
        if number > -1:
            result = result[0: number]
        #_logger.debug(NAME + " USING LOCAL FILTERING")
        #_logger.debug(NAME + " REQUESTED - " + str(toAsk))
        #_logger.debug(NAME + " RETURN FOR UNCHOKING - " + str(accepted))

        return result

class SameIPPrefixPolicy(RankingPolicy):
    
    def __init__(self, list_of_reference_ip_addr=[]):
        RankingPolicy.__init__(self)
        
        self.set_ip_prefixes(list_of_reference_ip_addr)
        assert len(self.ref_ip_addrs)>0, "no ip prefix set"
                
        #check provided ranges for consistency:
        for prefix in self.ref_ip_addrs:
            (ip, bitrange) = ipaddr_utils._extract_addr_and_bitrange(prefix)
            assert ipaddr_utils.validIP(ip) and bitrange>=0 and bitrange <=32, "Invalid ip range " + prefix 
        
        
        self._logger.info("Use IP prefix based policy with the prefixes: %s" % self.ref_ip_addrs)
    
    def set_ip_prefixes(self, ip_prefixes):
        self.ref_ip_addrs = [ip_addr for ip_addr in ip_prefixes if ipaddr_utils.is_reference_ip_addr_admissible(ip_addr)]
        self._logger.info("Set local ip prefixes to %s" % self.ref_ip_addrs)
    
    def getRankedPeers(self, iplist):
        res = dict()
        self._logger.debug("Peers to rank %s" % str(iplist))
        for ip in iplist:
            res[ip] = 0
            for reference_ip in self.ref_ip_addrs:
                if ipaddr_utils.matches_ip_prefix(ip, reference_ip):
                    res[ip] = 100
                    break
        self._logger.debug("Ranked vs prefixes %s as: %s" % (str(self.ref_ip_addrs), str(res)))
        return res