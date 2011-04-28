import logging, sys
import HAPService_client as WS

class HAP_WSClient(object):
    '''Defines the interface for communicating with the HAP endpoint.'''
    def __init__(self, hap_endpoint="http://localhost:8080/sis/HAPEndpoint", own_ip=None, own_port=5578):
        # default value of own_ip is None, since it is an optional field in the report.
        # own_ip cannot be determined reliably. the HAP server component should simply read
        # the IP address from the socket connection.
        self._hap_endpoint = hap_endpoint
        self._own_ip = own_ip
        self._own_port = own_port
        self._loc = WS.HAPServiceLocator()
        self._srv = self._loc.getHAPServicePort(self._hap_endpoint)
        self._logger = logging.getLogger("Client.HAP")
    
    def report_activity(self, neighbour_statistics):
        '''Reports neighbour activity to the HAP endpoint.
        
           Arguments:
                neighbour_statistics    --    List of HAPNeighbourStatistics objects
                
           Returns:
                NoneType
        '''
        peer_stats = HAPPeerStatisticsDTO(self._own_ip, neighbour_statistics, self._own_port)
        request = WS.SisHAPPort_reportActivity()
        request.set_element_arg0(peer_stats)
        self._logger.debug("Sending neighbour activity to HAP (%s)" % self._hap_endpoint)
        response = self._srv.reportActivity(request)
    
class HAPNeighbourStatisticsDTO(object):
    def __init__(self, downVolume, ipAddress, upVolume):
        '''Data transfer object for storing HAP neighbour statistics that are going to be sent
           as part of a HAPPeerStatistics object to the HAP endpoint.
           
           Arguments:
                downVolume        --        The total download volume for that neighbour
                upVolume          --        The total upload volume for that neighbour
                ipAddress         --        The IP address of the neighbour
        
           Returns:
                NoneType
        '''
        self._downVolume = downVolume
        self._ipAddress = ipAddress
        self._upVolume = upVolume
        
class HAPPeerStatisticsDTO(object):
    def __init__(self, ipAddress, neighbors, port):
        '''Data transfer object for storing HAP peer statistics that are going to be sent
           to the HAP endpoint.
           
           Arguments:
                ipAddress        --        The IP address of the sending peer
                port             --        The port address of the sending peer
                neighbors        --        List of HAPNeighbourStatistics objects
                
           Returns:
                NoneType
        '''
        self._ipAddress = ipAddress
        self._neighbors = neighbors
        self._port = port
        
if __name__ == "__main__":
    if len(sys.argv)==2:        
        SIS_URL=sys.argv[1]
    else:
        SIS_URL="http://localhost:8080"
    hap_endpoint = SIS_URL+"/sis/HAPEndpoint"
    print "use endpoint", hap_endpoint
    
    client = HAP_WSClient(hap_endpoint=hap_endpoint, own_ip=None, own_port=5578)
    neighbor = HAPNeighbourStatisticsDTO(100, "22.22.22.22", 200)
    #stats = HAPPeerStatisticsDTO("1.2.3.4", [neighbor], 12345)
    client.report_activity([neighbor])