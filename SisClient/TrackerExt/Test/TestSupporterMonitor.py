import unittest
import time

import SisClient.TrackerExt.SupporterMonitor as SupporterMonitor

__author__ = "Markus Guenther"


class TestMonitoredPeer(unittest.TestCase):
    def setUp(self):
        SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND = 2
        SupporterMonitor.PEER_TIMEOUT_BOUND = 1
    
    def tearDown(self):
        pass
    
    def testMonitoredPeerDefaults(self):
        '''Tests proper setup of a new MonitoredPeer instance (including defaults).
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10333, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertEquals('XXX---34920F', peer.get_id())
        self.assertEquals('192.168.2.1', peer.get_ip())
        self.assertEquals(10333, peer.get_port())
        self.assertEquals(SupporterMonitor.PEER_TYPE_LEECHER, peer.get_peer_type())
        # check default values
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        self.assertEquals(None, peer.get_ts_first_request())
        self.assertEquals(None, peer.get_ts_last_request())
        self.assertEquals(0, peer.get_number_of_support_requests())
        self.assertEquals(None, peer.get_last_received_msg())
        
    def testMonitoredPeerWithInvalidArguments(self):
        '''Tests instantiation of a MonitoredPeer with invalid arguments.
        '''
        try:
            _ = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 500, SupporterMonitor.PEER_TYPE_LEECHER)
            self.fail("The instantiation should have raised an AssertionError")
        except AssertionError:
            pass
        
    def testMonitoredPeerStateCorrectNextCycle(self):
        '''Tests if a peer can walk through two cycles.
        
        This test shows that the extended tracker monitors peer states correctly as they
        progress the state diagram. A peer transitions along the following path of states
        during this test:
        
        DEFAULT -> WATCHED -> DEFAULT -> WATCHED -> STARVING -> SUPPORTED -> DEFAULT
        
        The test also ensures that the internal attributes are set to the correct values
        after each state transition.
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        self.assertEquals(None, peer.get_ts_first_request())
        self.assertEquals(None, peer.get_ts_last_request())
        self.assertEquals(0, peer.get_number_of_support_requests())
        
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        self.assertNotEquals(None, peer.get_ts_first_request())
        self.assertNotEquals(None, peer.get_ts_last_request())
        self.assertEquals(peer.get_ts_first_request(), peer.get_ts_last_request())
        self.assertEquals(1, peer.get_number_of_support_requests())
        # new cycle has started
        for _ in xrange(5):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
            
        peer.receive_msg(SupporterMonitor.MSG_PEER_SUPPORTED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.SupportedState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        time.sleep(1)
        # this transition call would normally have to happen asynchronously through the
        # SupporterMonitor's cyclic transition check
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
    def testMonitoredPeerStateTransitionsEarlyCancel(self):
        '''Tests if a peer can cancel its request while being in WATCHED state.
        
        This test shows that the extended tracker monitors peer states correctly as they
        progress a part of the state diagram. A peer transitions along the following path of
        states during this test:
        
        DEFAULT -> WATCHED -> DEFAULT (early cancel due to sending of buffer full msg)
        
        The test also ensures that the internal attributes are set to the correct values
        after each state transition.
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        self.assertEquals(1, peer.get_number_of_support_requests())
        self.assertEquals(SupporterMonitor.MSG_SUPPORT_REQUIRED, peer.get_last_received_msg())
        self.assertNotEquals(None, peer.get_ts_first_request())
        self.assertNotEquals(None, peer.get_ts_last_request())
        self.assertEquals(peer.get_ts_first_request(), peer.get_ts_last_request())
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        self.assertEquals(0, peer.get_number_of_support_requests())
        self.assertEquals(None, peer.get_ts_first_request())
        self.assertEquals(None, peer.get_ts_last_request())
    
    def testMonitoredPeerStateTransitionsFull(self):
        '''Tests if a peer can transition through all states correctly.
        
        This test shows that the extended tracker monitors peer states correctly as they
        progress the state diagram completely. A peer transitions along the following path
        of states during this test:
        
        DEFAULT -> WATCHED -> STARVING -> SUPPORTED -> DEFAULT (on buffer full msg)
        
        The test also ensures that the internal attributes are set to the correct values
        after each state transition.
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertEquals(SupporterMonitor.MSG_SUPPORT_REQUIRED, peer.get_last_received_msg())
        self.assertEquals(1, peer.get_number_of_support_requests())
        self.assertNotEquals(None, peer.get_ts_first_request())
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        
        for _ in xrange(5):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
            
        self.assertEquals(SupporterMonitor.MSG_SUPPORT_REQUIRED, peer.get_last_received_msg())
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
        peer.receive_msg(SupporterMonitor.MSG_PEER_SUPPORTED)
        self.assertEquals(SupporterMonitor.MSG_PEER_SUPPORTED, peer.get_last_received_msg())
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.SupportedState))
        # TODO: also check with server side message (timeout)
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        self.assertEquals(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED, peer.get_last_received_msg())
        time.sleep(1)
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
    def testMonitoredPeerStateRequiredMsgsInIntervalNotMet(self):
        '''Tests if the time interval requirements for the transition from WATCHED to STARVING are met.
        
        This test simulates PEER_REQUIRED_MSGS support required message arrivals over a time period
        greater than the time window in which they should arrive, so that the transition from
        WATCHED to STARVING can be carried out. To pass this test, the peer should remain in
        the WATCHED state after the last message was received.
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS-1):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        time.sleep(SupporterMonitor.PEER_STATUS_APPROVAL_TIME+1)
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        # although we have now received PEER_REQUIRED_MSGS support messages, the peer has not
        # transitioned to the starving state, since those messages arrived over a time which
        # is greater than the calculated time bound in which they should have arrived
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        
    def testSlidingWindowOnRequestTime(self):
        '''Checks if the sliding window for arrived support requests works correctly.'''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS-1):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        time.sleep(SupporterMonitor.PEER_STATUS_APPROVAL_TIME+1)
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
        
    def testPeerTimesOut(self):
        '''Test transitions from {WATCHED,STARVING,SUPPORTED} to DEFAULT.
        
        In the implementation, the timeout is only relevant if we want to transition
        from SUPPORTED to DEFAULT. Transitions from {WATCHED,STARVING} to DEFAULT
        should happen instantaneously if the peer informs the SupporterMonitor that
        his buffer is full.
        '''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        
        # test the transition on buffer full + timeout from WATCHED -> DEFAULT
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
        # test the transition on buffer full + timeout from STARVING -> DEFAULT
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
        # test the transition on buffer full + timeout from SUPPORTED -> DEFAULT
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
        peer.receive_msg(SupporterMonitor.MSG_PEER_SUPPORTED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.SupportedState))
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED)
        time.sleep(SupporterMonitor.PEER_TIMEOUT_BOUND)
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
    def testEqualityTest(self):
        '''Tests if two monitored peers with same static attributes are considered equal.'''
        p1 = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        p2 = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertEquals(p1, p2)
        
    def testPeerIsAliveTriggersStateTransitionsCorrectly(self):
        '''Tests if peer states transition back to DEFAULT state if peer is considered as not being alive.'''
        peer = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.1', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        peer.receive_msg(SupporterMonitor.MSG_PEER_REGISTERED)
        
        # transition from WATCHED -> DEFAULT on is-alive timeout
        peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.WatchedState))
        time.sleep(SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND)
        self.assertFalse(peer.peer_is_alive())
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
        # transition from STARVING -> DEFAULT on is-alive timeout
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.StarvingState))
        time.sleep(SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND)
        self.assertFalse(peer.peer_is_alive())
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
        # transition from SUPPORTED -> DEFAULT on is-alive timeout
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            peer.receive_msg(SupporterMonitor.MSG_SUPPORT_REQUIRED)
        peer.receive_msg(SupporterMonitor.MSG_PEER_SUPPORTED)
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.SupportedState))
        time.sleep(SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND)
        peer.get_state().transition()
        self.assertTrue(isinstance(peer.get_state(), SupporterMonitor.DefaultState))
        
class TestMonitoredSupporter(unittest.TestCase):
    def setUp(self):
        SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND = 2
        SupporterMonitor.PEER_TIMEOUT_BOUND = 1
    
    def tearDown(self):
        pass
    
    def testInstantiationWithCorrectParameters(self):
        '''Tests if the instantiation of MonitoredSupporter works, given correct parameters.'''
        supporter = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1024), 3, 5)
        self.assertEquals(('192.168.2.1', 1024), supporter.get_addr())
        self.assertEquals(1, supporter.get_id())
        self.assertEquals(3, supporter.get_min_peer())
        self.assertEquals(5, supporter.get_max_peer())
        self.assertEquals(5, supporter.available_slots())
        self.assertEquals(0, supporter.assigned_slots())
        
    def testInstantiationWithIncorrectParameters(self):
        '''Tests if the instantiation of MonitoredSupporter fails correctly, given wrong parameters.'''
        try:
            _ = SupporterMonitor.MonitoredSupporter(1, None, 3, 5)
            self.fail("Supporter address incorrect. Expected: (ip,port) tuple, given: None")
        except AssertionError:
            pass
        
        try:
            _ = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1000), 3, 5)
            self.fail("Port number incorrect. Expected: port >= 1024, given: 1000")
        except AssertionError:
            pass
        
        try:
            _ = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1024), 5, 4)
            self.fail("min-/max_peers wrong. Expected: min_peers <= max_peers, given: 5 > 4")
        except AssertionError:
            pass
        
    def testMaintainSupporteeList(self):
        '''Tests if the maintenance of the supportee list works correctly.'''
        supporter = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1024), 2, 5)
        p1 = SupporterMonitor.MonitoredPeer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        p2 = SupporterMonitor.MonitoredPeer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        p3 = SupporterMonitor.MonitoredPeer('XXX---34920H', '192.168.2.52', 10002, SupporterMonitor.PEER_TYPE_LEECHER)
        supporter.add_supported_peer(p1)
        self.assertFalse(supporter.minimum_starving_peers_reached())
        supporter.add_supported_peer(p2)
        self.assertEquals(2, supporter.assigned_slots())
        self.assertEquals(3, supporter.available_slots())
        self.assertTrue(supporter.minimum_starving_peers_reached())
        supporter.add_supported_peer(p3)
        self.assertEquals(3, supporter.assigned_slots())
        self.assertEquals(2, supporter.available_slots())
        supporter.remove_supported_peer(p1)
        self.assertEquals(2, supporter.assigned_slots())
        self.assertEquals(3, supporter.available_slots())
        supporter.remove_supported_peer(p2)
        self.assertEquals(1, supporter.assigned_slots())
        self.assertEquals(4, supporter.available_slots())
        # TODO: see remark in MonitoredSupporter.inactivate
        self.assertFalse(supporter.minimum_starving_peers_reached())

    def testEqualityTest(self):
        '''Tests if two monitored supporters with same static attributes are considered equal.'''
        s1 = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1024), 2, 5)
        s2 = SupporterMonitor.MonitoredSupporter(1, ('192.168.2.1', 1024), 2, 5)
        self.assertEquals(s1, s2)
        
class TestSupporterMonitor(unittest.TestCase):
    def setUp(self):
        SupporterMonitor.IS_ALIVE_TIMEOUT_BOUND = 2
        SupporterMonitor.PEER_TIMEOUT_BOUND = 1
    
    def tearDown(self):
        pass
    
    def testUnregisterMonitoredPeers(self):
        '''Tests if peers can be properly unregistered from a SupporterMonitor instance.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        mp1 = monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        mp2 = monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        self.assertTrue(len(monitor.get_monitored_peers()) == 2)
        monitor.unregister_monitored_peer(mp1)
        self.assertTrue(len(monitor.get_monitored_peers()) == 1)
        monitor.unregister_monitored_peer(mp2)
        self.assertTrue(len(monitor.get_monitored_peers()) == 0)
    
    def testPeersRemainInStarvingState(self):
        '''Peers remain in STARVING state if no supporter can be activated.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_supporter(1, ('192.168.2.10', 1024), 3, 5)

        monitor.update_states()
        
        self.assertTrue(len(monitor.get_monitored_peers()) == 2)
        self.assertTrue(len(monitor.get_monitored_supporters()) == 1)
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.DefaultState)) == 2)
        
        for _ in xrange(5):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920F')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920G')
        monitor.update_states()
            
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 2)
    
    def testSimpleProtocol(self):
        '''Simple test for correct supporter assignments, state transitions and supporter activations.''' 
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_supporter(1, ('192.168.2.1', 1024), 2, 5)
        
        self.assertTrue(len(monitor.get_monitored_peers()) == 1)
        self.assertTrue(len(monitor.get_monitored_supporters()) == 1)
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.DefaultState)) == 1)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 0)
        
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920F')
            
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 1)
        
        monitor.update_states()
                
        monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920G')
            
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 2)
        
        monitor.update_states()
        
        self.assertTrue(len(monitor.get_active_supporters()) == 1)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 2)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 0)
        
        monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED, 'XXX---34920F')
        monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_NOT_NEEDED, 'XXX---34920G')
        time.sleep(SupporterMonitor.PEER_TIMEOUT_BOUND)
        
        monitor.update_states()
        
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.DefaultState)) == 2)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 0)
        
    def testActivatingMoreThanOneSupporterAtOnce(self):
        '''Checks if we can activate more than one supporter during one monitor state update.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        monitor.register_monitored_supporter(1, ('192.168.2.10', 5000), 2, 2)
        monitor.register_monitored_supporter(2, ('192.168.2.11', 5001), 1, 1)
        monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920H', '192.168.2.52', 10002, SupporterMonitor.PEER_TYPE_LEECHER)
        
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920F')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920G')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920H')
        
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 3)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 0)
        
        monitor.update_states()
        
        self.assertTrue(len(monitor.get_active_supporters()) == 2)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 3)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 0)
        
    def testActivateOneSupporterFromMultipleInactiveSupporters(self):
        '''Checks if the activation algorithm considers min_peers/max_peers together.
        
        The outcome of the test should be, that only one of the two available supporters
        is activated. If the activation algorithm just focuses on min_peers, it will
        activate both supporters, which should not happen.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        monitor.register_monitored_supporter(1, ('192.168.2.10', 5000), 2, 3)
        monitor.register_monitored_supporter(2, ('192.168.2.11', 5001), 1, 3)
        monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920H', '192.168.2.52', 10002, SupporterMonitor.PEER_TYPE_LEECHER)

        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920F')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920G')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920H')
        
        self.assertTrue(len(monitor.get_active_supporters()) == 0)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 3)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 0)
        
        monitor.update_states()
        
        self.assertTrue(len(monitor.get_active_supporters()) == 1)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.SupportedState)) == 3)
        self.assertTrue(len(monitor.filter_peers_by_state(SupporterMonitor.StarvingState)) == 0)
    
    def testCorrectOrderOfActiveSupporters(self):
        '''Checks if the ordering of active supporters is correct.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        s1 = monitor.register_monitored_supporter(1, ('192.168.2.50', 5000), 1, 1)
        s2 = monitor.register_monitored_supporter(2, ('192.168.2.51', 5001), 1, 6)
        monitor.register_monitored_peer('XXX---34920F', '192.168.2.50', 10000, SupporterMonitor.PEER_TYPE_LEECHER)
        monitor.register_monitored_peer('XXX---34920G', '192.168.2.51', 10001, SupporterMonitor.PEER_TYPE_LEECHER)
        
        for _ in xrange(SupporterMonitor.PEER_REQUIRED_MSGS):
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920F')
            monitor.received_peer_message(SupporterMonitor.MSG_SUPPORT_REQUIRED, 'XXX---34920G')
        monitor.update_states()
        
        self.assertTrue(len(monitor.get_active_supporters()) == 2)
        self.assertEquals(monitor.get_active_supporters()[0], s2)
        self.assertEquals(monitor.get_active_supporters()[1], s1)
        
    def testUpdateCallWithoutHavingPeersOrSupportersSucceeds(self):
        '''Tests if the update call succeeds if no peers/supporters are registered.
        
        Actually, there was a bug that was seen during writing the tracker integration code that
        was caused when update_states() was called when no peers/supporters were registered
        at the monitor. This test remains in the testsuite, so that this bug will not get
        introduced again.'''
        monitor = SupporterMonitor.SupporterMonitor()
        monitor._dispatcher = MockSupporteeListDispatcher(monitor)
        monitor.update_states()
        
#___________________________________________________________________________________________________
#

class MockSupporteeListDispatcher():
    def __init__(self, monitor):
        assert isinstance(monitor, SupporterMonitor.SupporterMonitor)
        
        self._monitor = monitor
        
    def register_proxy(self, supporter):
        assert isinstance(supporter, SupporterMonitor.MonitoredSupporter)

        
    def unregister_proxy(self, supporter):
        assert isinstance(supporter, SupporterMonitor.MonitoredSupporter)
    
    def dispatch_peer_lists(self):
        pass
    
    def query_all_supporters(self):
        pass
        
#___________________________________________________________________________________________________
# MAIN
        
if __name__ == "__main__":
    suite_peer = unittest.TestLoader().loadTestsFromTestCase(TestMonitoredPeer)
    suite_supporter = unittest.TestLoader().loadTestsFromTestCase(TestMonitoredSupporter)
    suite_monitor = unittest.TestLoader().loadTestsFromTestCase(TestSupporterMonitor)
    suite = unittest.TestSuite([suite_peer, suite_supporter, suite_monitor])
    unittest.TextTestRunner(verbosity=2).run(suite)