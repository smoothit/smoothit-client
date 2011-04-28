from SisClient.Client.ClientCallbackHandlers import ClientHAPHandler

import unittest

class TestClientHAPHandler(unittest.TestCase):
    
    def testAggregateTotalTraffic(self):
        torrent_id_a = "some_torrent"
        torrent_id_b = "another_torrent"
        peer_id = "127.0.0.1"
        
        hap_handler = ClientHAPHandler()
        hap_handler._update_volume(torrent_id_a, peer_id, 1024.0, 1024.0)
        hap_handler._update_volume(torrent_id_b, peer_id, 2048.0, 2048.0)
        
        dtotal, utotal = hap_handler.aggregate_total_peer_traffic(peer_id)
        
        self.assertEquals(3, dtotal)
        self.assertEquals(3, utotal)
        self.assertTrue(peer_id in hap_handler._neighbour_ips)
        self.assertTrue(len(hap_handler._neighbour_ips) == 1)
    
    def testCorrectDictUpdate(self):
        
        torrent_id = "some_torrent"
        peer_id_a = "127.0.0.1"
        peer_id_b = "183.132.13.39"
        
        hap_handler = ClientHAPHandler()
        hap_handler._update_volume(torrent_id, peer_id_a, 1024.0, 2048.0)
        hap_handler._update_volume(torrent_id, peer_id_b, 512.0, 512.0)
        
        self.assertTrue(len(hap_handler._neighbour_ips) == 2)
        self.assertTrue(peer_id_a in hap_handler._neighbour_ips)
        self.assertTrue(peer_id_b in hap_handler._neighbour_ips)
        
        self.assertTrue(hap_handler._neighbours.has_key(torrent_id))
        self.assertTrue(hap_handler._neighbours[torrent_id].has_key(peer_id_a))
        self.assertTrue(hap_handler._neighbours[torrent_id].has_key(peer_id_b))
        self.assertEquals(1, len(hap_handler._neighbours))
        self.assertEquals(2, len(hap_handler._neighbours[torrent_id]))
        self.assertEquals(2, hap_handler._neighbours[torrent_id][peer_id_a]['upload'])
        self.assertEquals(1, hap_handler._neighbours[torrent_id][peer_id_a]['download'])
        self.assertEquals(0, hap_handler._neighbours[torrent_id][peer_id_b]['upload'])
        self.assertEquals(0, hap_handler._neighbours[torrent_id][peer_id_b]['download'])
        
        hap_handler._update_volume(torrent_id, peer_id_a, 2048.0, 4096.0)
        hap_handler._update_volume(torrent_id, peer_id_b, 2048.0, 4096.0)
        
        # new reports for already seen IP addresses should have no effect on the
        # neighbour ips list
        self.assertTrue(len(hap_handler._neighbour_ips) == 2)
        self.assertTrue(peer_id_a in hap_handler._neighbour_ips)
        self.assertTrue(peer_id_b in hap_handler._neighbour_ips)
        
        self.assertEquals(4, hap_handler._neighbours[torrent_id][peer_id_a]['upload'])
        self.assertEquals(2, hap_handler._neighbours[torrent_id][peer_id_a]['download'])
        self.assertEquals(4, hap_handler._neighbours[torrent_id][peer_id_b]['upload'])
        self.assertEquals(2, hap_handler._neighbours[torrent_id][peer_id_b]['download'])
    
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientHAPHandler)
    unittest.TextTestRunner(verbosity=2).run(suite)