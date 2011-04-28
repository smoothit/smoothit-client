class IopApi():
    '''Defines the interface for selection strategies.
    '''
    def __init__(self):
        #self._sis_iop_endpoint_url = sis_iop_endpoint_url
        pass
    
    def report_activity(self, ip_addr, port, downloads):
        '''Dispatches activity reports to the SIS server.
        
        Arguments:
            ip_addr    -- The IP address of the peer that sends the activity report.
            port       -- The assigned network port of the peer that sends the activity report.
            downloads  -- List of tuples of the form (torrent_id, torrent_url, filesize, progress),
                          where:
                          torrent_id    -- Hash info of the corresponding torrent (String-valued)
                          torrent_url   -- URL where the corresponding torrent is located (String-
                                           valued)
                          filesize      -- The filesize of the corresponding file in bytes
                          progress      -- Indicates the progress of the download (value in [0..1])
            
        Returns:
            NoneType
        '''
        pass
    
    def retrieve_torrent_stats(self, max_requested_torrents=10):
        '''Returns torrent popularity statistics based on previous client requests.
        
        Arguments:
            max_requested_torrents    -- The maximum number of torrent statistics the IoP client
                                         wants to receive. Please note that this is an upper bound
                                         on the torrent statistics the client will receive.
        
        Returns:
            List of tuples of the form (torrent_id, torrent_url, rate)
        '''
        pass
    
    def retrieve_local_peers_for_active_torrents(self,
                                                 list_of_torrent_ids = [],
                                                 maximum_number_of_peers = 10,
                                                 include_seeds = False):
        '''The IoP client sends the information in which current swarms it participates to the
        SIS server, requesting information about local peers that also participate in those
        swarms (if known by the SIS).
        
        Arguments:
            list_of_torrent_ids     -- List that contains String-valued torrent hash infos (in hex encoding as exchanged with SIS!)
            maximum_number_of_peers -- The maximum amount of peers the reply shall include
            include_seeds           -- A flag denoting whether seeds should be included in the
                                       reply list
        
        Returns:
            A dict with torrent ids as keys and a list of 2-tuples of the form
            (peer_ip_addr, peer_port) as corresponding values.
        '''
        pass
    
    def retrieve_configuration_parameters(self, my_own_ip="127.0.0.1"):
        '''Retrieves the configuration parameters for the IoP functionality.
        
        Arguments:
            my_own_ip    -- The IP address of the IoP client
            
        Returns:
            A dict with parameter names (String-valued) as keys. Corresponding values are
            already converted to the correct data type.
        '''
        pass
