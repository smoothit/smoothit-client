import logging
import threading
import time
import xmlrpclib
import sys

__author__ = "Markus Guenther"

PEER_TIMEOUT_BOUND = 5 # seconds (should not be set too high!)
IS_ALIVE_TIMEOUT_BOUND = 10 # every peer transitions back to default state if it has not send
                            # any messages for IS_ALIVE_TIMEOUT_BOUND seconds
PEER_REQUIRED_MSGS = 5
# the underneath parameters represents the time interval in which a peer has to send its
# requests, so it can transition to the STARVING state. the value is based on the total number
# of required requests (for every request, we assume 1 second), and a typical RTT value which
# is taken into account for every made request)
PEER_STATUS_APPROVAL_TIME = PEER_REQUIRED_MSGS * ( 1 + 0.150 )
PEER_REMOVAL_TIME = 20 # removes a monitored peer if the last activity was reported more 
#than PEER_REMOVAL_TIME seconds ago

PEER_TYPE_SEEDER = 0
PEER_TYPE_LEECHER = 1
PEER_TYPES = [ PEER_TYPE_SEEDER, PEER_TYPE_LEECHER ]

MSG_SUPPORT_REQUIRED = "support_required"
MSG_SUPPORT_NOT_NEEDED = "support_not_needed"
MSG_PEER_SUPPORTED = "peer_supported"
MSG_PEER_REGISTERED = "peer_registered"

#___________________________________________________________________________________________________

class State(object):
    '''State is the abstract base class for all states that can be assigned to a monitored
    peer. There is a bidirectional dependency between State and MonitoredPeer, so each
    MonitoredPeer knows its state, and each State knows the MonitoredPeer it belongs to.'''
    def __init__(self, monitored_peer):
        assert monitored_peer is not None
        self._monitored_peer = monitored_peer
        
    def get_monitored_peer(self):
        '''
        @return: The associated MonitoredPeer object
        '''
        return self._monitored_peer
    
    def transition(self):
        '''Checks if a transition to successor states is possible from the current state
        and performs this transition. This method has to be overriden in implementing classes.

        @return:
            NoneType
        '''
        pass
    
    def __str__(self):
        pass
    
class DefaultState(State):
    '''Realizes the DEFAULT state of a MonitoredPeer as described in (Gerlach, 2010). Every newly
    registered peers starts out in this state and returns back to it, once it does not need any
    further support.
    '''
    def __init__(self, monitored_peer):
        State.__init__(self, monitored_peer)
        
    def transition(self):
        '''Checks if the MonitoredPeer can transition to the WATCHED state. See State.transition
        for further documentation.
        
        @return: 
            NoneType
        '''
        m = self.get_monitored_peer()
        if m.get_ts_first_request()  is not None and m.get_number_of_support_requests() == 1:
            m.set_state(WatchedState(m))
            
    def __str__(self):
        return 'Default'
            
class WatchedState(State):
    '''Realizes the WATCHED state of a MonitoredPeer as described in (Gerlach, 2010). The
    implementation deviates from the before mentioned work since it also allows to transition
    back to the DEFAULT state from WATCHED state.
    '''
    def __init__(self, monitored_peer):
        State.__init__(self, monitored_peer)
        
    def transition(self):
        '''Checks if the MonitoredPeer can transition back to the DEFAULT state or forward
        to the STARVING state. The transition to the DEFAULT state happens immediately and thus
        does not rely on the peer timeout as defined in module SupporterMonitor 
        (cf. constant PEER_TIMEOUT_BOUND). For the transition to the STARVING state, a certain number
        of support requests (cf. constant PEER_REQUIRED_MSGS) have to be arrived in a certain time
        window (cf. constant PEER_STATUS_APPROVAL_TIME).
        
        @return:
            NoneType
        '''
        m = self.get_monitored_peer()
        
        if not m.peer_is_alive():
            m.set_state(DefaultState(m))
            m.reset_support_cycle()
        elif m.get_last_received_msg() == MSG_SUPPORT_NOT_NEEDED:
            # the transition from WATCHED -> DEFAULT is not dependent on the timeout
            m.set_state(DefaultState(m))
        elif m.get_last_received_msg() == MSG_SUPPORT_REQUIRED:
            # this is the regular case
            # TODO: any special cases that require knowledge of the whole system, should be
            # applicated in the SupporterMonitor class directly after updating individual peer
            # states
            if (m.get_ts_last_request() - m.get_ts_first_request()) <= PEER_STATUS_APPROVAL_TIME and \
                m.get_number_of_support_requests() >= PEER_REQUIRED_MSGS:
                m.set_state(StarvingState(m))
                
    def __str__(self):
        return 'Watched'
        
class StarvingState(State):
    '''Realizes the STARVING state of a MonitoredPeer as described in (Gerlach, 2010). The
    implementation deviates from the before mentioned work since it also allows to transition
    back to the DEFAULT state from STARVING state.
    '''
    def __init__(self, monitored_peer):
        State.__init__(self, monitored_peer)
        
    def transition(self):
        '''Checks if the associated MonitoredPeer can transition back to the DEFAULT state
        (in case the support is no longer required) or transition forward to the SUPPORTED
        state. The transition to the DEFAULT state happens immediately and thus does not
        rely on the peer timeout as defined in module SupporterMonitor (cf. constant
        PEER_TIMEOUT_BOUND). For the transition to the SUPPORTED state, the peer has to 
        receive the supported message from the SupporterMonitor beforehand.
        
        @return:
            NoneType
        '''
        m = self.get_monitored_peer()
        msg_type = m.get_last_received_msg()
        
        if not m.peer_is_alive():
            m.set_state(DefaultState(m))
            m.reset_support_cycle()
        elif msg_type == MSG_SUPPORT_NOT_NEEDED:
            # the transition from STARVING -> DEFAULT is not dependent on the timeout
            # TODO (kp): should apply it only when single supporters is available?
            m.set_state(DefaultState(m))        
        
        if msg_type == MSG_PEER_SUPPORTED:
            m.set_state(SupportedState(m))
            
    def __str__(self):
        return 'Starving'
        
class SupportedState(State):
    '''Realizes the SUPPORTED state of a MonitoredPeer as described in (Gerlach, 2010).
    '''
    def __init__(self, monitored_peer):
        State.__init__(self, monitored_peer)
        
    def transition(self):
        '''Checks if the associated MonitoredPeer can transition back to the DEFAULT state.
        This transition occurs, if the peer does not longer rely on the support of a 
        server and waited some more time after the NO SUPPORT REQUIRED message was received by
        the SupporterMonitor in the current state.
        
        @return:
            NoneType
        '''
        m = self.get_monitored_peer()
        msg_type = m.get_last_received_msg()
        
        if not m.peer_is_alive():
            m.set_state(DefaultState(m))
            m.reset_support_cycle()
        elif msg_type == MSG_SUPPORT_NOT_NEEDED and m.peer_timed_out() or not m.peer_is_alive():
            m.set_state(DefaultState(m))
            
    def __str__(self):
        return 'Supported'
            
#___________________________________________________________________________________________________

class MonitoredPeer(object):
    '''The MonitoredPeer class represents the local state of a peer as seen by the SupporterMonitor.
    It handles incoming messages and triggers state transitions as appropriate.
    
    MonitoredPeer keeps track of the last PEER_REQUIRED_MSGS that were forwarded from a
    SupporterMonitor instance to it (sliding window over all received messages).'''
    def __init__(self, id, ip, port, peer_type):
        self._last_received_msg = None
        self._ts_last_received_msg = None # there is a difference between the request message window
                                          # and this one here! (this is set for ALL message types)
        self._state = DefaultState(self)
        self._timeout_timer = None
        self.reset_support_cycle()
        # assign given parameters using class methods (they perform further checks on validity)
        self.set_id(id)
        self.set_ip(ip)
        self.set_port(port)
        self.set_peer_type(peer_type)
        
        self.msg_handler = { MSG_PEER_SUPPORTED            : self.received_peer_supported_message,
                             MSG_SUPPORT_NOT_NEEDED        : self.received_support_not_needed_message,
                             MSG_SUPPORT_REQUIRED          : self.received_support_required_message,
                             MSG_PEER_REGISTERED           : self.received_peer_registered_message }
        
    def __hash__(self):
        '''The hash of a MonitoredPeer is based on the peer's ID and its address. The implementation
        utilizes the hash function on Python's tuple data type to generate the hash value for
        a MonitoredPeer object.
        
        @return:
            Hash value based on the 3-tuple (ID, IP, Port)
        '''
        return hash((self._id, self._ip, self._port))
    
    def __eq__(self, other):
        '''Equality test on two MonitoredPeer instances. The test is based on the comparison of
        the objects hash values and therefore solely relies on the 3-tuple (ID, IP, Port).
        
        @param other:
            Another instance of MonitoredPeer to which this instance shall be compared to
        
        @return:
            Boolean value indicating whether two instances represent the same state of information.
        '''
        assert isinstance(other, MonitoredPeer)
        return self.__hash__() == other.__hash__()
    
    def get_ts_last_message(self):
        '''@return:
            The timestamp of the last message (over all message types, not just the request
            messages, as in the sliding window over all requests!) that was received.
        '''
        return self._ts_last_received_msg
        
    def get_ts_first_request(self):
        '''@return:
            The timestamp of the first message in the sliding window over the last
            PEER_REQUIRED_MSGS. NoneTyp if no messages were received prior to the call
            of this method. Please be aware that the returned value of get_ts_last_request
            equals the return value of get_ts_first_request if there was only one message
            receive prior the resp. method call.
        '''
        if len(self._ts_list) == 0:
            return None
        return self._ts_list[0]
    
    def get_ts_last_request(self):
        '''@return:
            The timestamp of the last message in the sliding window over the last
            PEER_REQUIRED_MSGS. NoneType if no messages were received prior to the call
            of this method. Please be aware that the returned value of get_ts_last_request
            equals the return value of get_ts_first_request if there was only one message
            receive prior the resp. method call.
        '''
        if len(self._ts_list) == 0:
            return None
        return self._ts_list[len(self._ts_list)-1]
    
    def get_number_of_support_requests(self):
        '''@return:
            The number of support requests by this peer during the current admission cycle
        '''
        return self._support_requests
    
    def increment_support_requests(self):
        '''Increments the number of support requests. Triggered upon the receipt of a support
        message.
        
        @return:
            NoneType
        '''
        self._support_requests += 1
        
    def reset_support_cycle(self):
        '''Resets the support cycle, which results in the deletion of the last PEER_REQUIRED_MSGS
        (the sliding window over the last received messages is empty afterwards) and the reset of
        the number of support requests to its initial value of 0.
        
        @return:
            NoneType
        '''
        self._ts_list = []
        self._support_requests = 0
        
    def set_id(self, id):
        '''Sets the ID for this MonitoredPeer instance.
        
        @param id:
            The ID of the associated peer
        
        @return:
            NoneType
        '''
        # TODO (mgu): Since the ID is considered a static attribute, it should only be set during 
        # the instantiation of the object
        self._id = id
        
    def get_id(self):
        '''@return:
            The ID of the associated MonitoredPeer instance.
        '''
        return self._id
    
    def set_ip(self, ip):
        '''Sets the IP address for this MonitoredPeer instance.
        
        @param ip:
            The IP address of the associated peer
        
        @return:
            NoneType
        '''
        # TODO (mgu): Since the IP address is considered a static attribute, it should only be
        # set during the instantiation of the object
        self._ip = ip
        
    def get_ip(self):
        '''@return:
            The IP address of the associated MonitoredPeer instance.
        '''
        return self._ip
    
    def set_port(self, port):
        '''Sets the port address of the associated MonitoredPeer instance. Asserts that the
        given port is >= 1024 (given port must be out of the range of reserved ports).
        
        @param port:
            The port address of the associated peer
        
        @return:
            NoneType
        '''
        # TODO (mgu): Since the port address is considered a static attribute, it should only be
        # set during the instantiation of the object
        assert port >= 1024
        self._port = port
        
    def get_port(self):
        '''@return:
            The port address of the associated MonitoredPeer instance.
        '''
        return self._port
    
    def set_peer_type(self, peer_type):
        '''Sets the peer type.
        
        @param peer_type:
            Parameter that describes the behaviour of the associated peer.
            The given value must be in [PEER_TYPE_LEECHER, PEER_TYPE_SEEDER].
        
        @return:
            NoneType
        '''
        assert peer_type in PEER_TYPES
        self._peer_type = peer_type
        
    def get_peer_type(self):
        '''Returns:
            The peer type of the associated MonitoredPeer instance
        '''
        return self._peer_type
    
    def set_state(self, state):
        '''Sets the current state of the MonitoredPeer instance. The given state must be
        a subclass of SupporterMonitor.State.
        
        @param state:
            Instance of a subclass of SupporterMonitor.State, representing
            the state that the associated peer resides in
        
        @return:
            NoneType
        '''
        assert isinstance(state, State)
        self._state = state
        
    def get_state(self):
        '''@return:
            The current state of the MonitoredPeer instance.
        '''
        return self._state
    
    def get_last_received_msg(self):
        '''@return:
            The type of the last received message. Return values are in [MSG_PEER_SUPPORTED,
            MSG_SUPPORT_NOT_NEEDED, MSG_SUPPORT_REQUIRED].
        '''
        return self._last_received_msg
    
    def peer_timed_out(self):
        '''Checks if the associated MonitoredPeer suffers from a timeout.
        
        The difference between peer_timed_out and peer_is_alive is simply the fact, that a peer
        has to remain in the SUPPORTED state for a short period of time, even if it does not
        need support any longer. peer_timed_out checks for this timeout. peer_is_alive on the
        other hand, checks, if the peer should transition back from any state to DEFAULT
        state after a while.
        
        @return:
            Boolean value, indicating whether the peer timed out
        '''
        if self.timeout_timer_stopped():
            return False
        return (time.time() - self._timeout_timer) >= PEER_TIMEOUT_BOUND
    
    def peer_is_alive(self):
        '''Checks if the associated MonitoredPeer is considered as being alive or not.
        
        The difference between peer_timed_out and peer_is_alive is simply the fact, that a peer
        has to remain in the SUPPORTED state for a short period of time, even if it does not
        need support any longer. peer_timed_out checks for this timeout. peer_is_alive on the
        other hand, checks, if the peer should transition back from any state to DEFAULT
        state after a while.
        '''
        
        if self.get_ts_last_request() is not None:
            return (time.time() - self.get_ts_last_request()) < IS_ALIVE_TIMEOUT_BOUND
        else:
            # if last_request_ts is NoneType, then the peer was just added to the monitor
            # and we have to wait a bit until it actually has send its first message
            return True
    
    def receive_msg(self, msg_type):
        '''Handler method which gets called whenever a message from a monitored peer was received.
        The method sets the internal state accordingly, calls the appropriate specific message
        handler method as defined in MonitoredPeer.msg_handler and triggers the synchronous
        transition of the current state.
        
        @param msg_type:
            Represents the message type of the received message. The given
            value must be in [MSG_PEER_SUPPORTED, MSG_SUPPORT_NOT_NEEDED,
            MSG_SUPPORT_REQUIRED].
        
        @return:
            NoneType
        '''
        assert msg_type in [ MSG_PEER_SUPPORTED, MSG_SUPPORT_NOT_NEEDED, MSG_SUPPORT_REQUIRED,
                             MSG_PEER_REGISTERED ]
        self._last_received_msg = msg_type
        self._ts_last_received_msg = time.time()
        self.msg_handler[msg_type]()
        self.get_state().transition()
        
    def support_aborted(self):
        '''Resets the peers state. This may occur the supporter the peer is assigned to
        is no longer reachable. The peers state will be set to STARVING STATE.
        
        @return:
            NoneType
        '''
        self._state = StarvingState(self)
    
    def received_support_required_message(self):
        '''Handler method for the event that the associated monitored peer sent MSG_SUPPORT_REQUIRED.
        The method updates the internal state as appropriate (timeout handling, sliding window
        update, support requests made update).
        
        @return:
            NoneType
        '''
        self.increment_support_requests()
        self.stop_timeout_timer()
        
        self._ts_list.append(time.time())
        
        if len(self._ts_list) > PEER_REQUIRED_MSGS:
            # slide one step further
            self._ts_list = self._ts_list[1:]
            
    def received_support_not_needed_message(self):
        '''Handler method for the event that the associated monitored peer sent
        MSG_SUPPORT_NOT_NEEDED. The method triggers the reset of the current admission cycle
        and starts a timeout timer which is needed for asynchronous state transitions.
        
        @return:
            NoneType
        '''
        self.reset_support_cycle()
        self.start_timeout_timer()
        
    def received_peer_supported_message(self):
        '''Handler method for the event that SupporterMonitor assigned the MonitoredPeer to
        a supporter server. The implementation does nothing at the moment.
        
        @return:
            NoneType
        '''
        pass
    
    def received_peer_registered_message(self):
        '''Handler method for the event that SupporterMonitor has just registered the
        associated peer. The implementation does nothing at the moment.
        
        @return:
            NoneType
        '''
        pass
    
    def start_timeout_timer(self):
        '''Starts a timeout timer (if it wasn't started before).
        
        @return:
            NoneType
        '''
        if self._timeout_timer == None:
            self._timeout_timer = time.time()
    
    def stop_timeout_timer(self):
        '''Stops the timeout timer.
        
        @return:
            NoneType
        '''
        self._timeout_timer = None
        
    def timeout_timer_stopped(self):
        '''@return:
            Boolean value, indicating whether the timeout timer is stopped.
        '''
        return self._timeout_timer == None
    
#___________________________________________________________________________________________________
    
class MonitoredSupporter(object):
    '''The MonitoredSupporter class represents the local state of a monitored supporter as seen
    by the SupporterMonitor. It basically is a wrapper for some attributes, implements logic
    to maintain an internal supportee list (starving peers get assigned to a supporter) and is
    able to differentiate between active and inactive supporter states.
    '''
    def __init__(self, id, addr, min_peer, max_peer):
        self._id = id
        assert isinstance(addr, tuple)
        assert len(addr) == 2
        assert addr[1] >= 1024
        self._addr = addr
        assert min_peer <= max_peer
        self._min_peer = min_peer
        self._max_peer = max_peer
        self._supported_peers = [] # holds MonitoredPeer instances
        global supported_peers
        supported_peers = self._supported_peers
        #self._is_active = False
        self._updated = True
                
    def __hash__(self):
        '''The hash of a MonitoredSupporter is based on the supporter's static attributes: its
        internal ID (we use the swarm-related peer ID, but any ID will do), its address in terms
        of IP address and port number, and the minimum and maximum amount of peers it can supply.
        The implementation utilizes Python's hash function on a newly constructed tuple that
        covers all static attributes.
        
        @return:
            Hash value based on the 4-tuple (ID, address, min_peer, max_peer)
        '''
        return hash((self._id, self._addr, self._min_peer, self._max_peer))
    
    def __eq__(self, other):
        '''Equality test on two MonitoredSupporter instances. The test is based on the comparison
        of the objects hash values as returned by __hash__ and therefore solely relies on the
        4-tuple (ID, address, min_peer, max_peer).
        
        @param other:
            Another instance of MonitoredSupporter that shall be compared to this instance
        
        @return:
            Boolean value indicating whether two instances represent the same state of information.
        '''
        assert isinstance(other, MonitoredSupporter)
        return self.__hash__() == other.__hash__()
        
    def get_id(self):
        '''@return:
            The ID of the associated monitored supporter
        '''
        return self._id
    
    def get_addr(self):
        '''@return:
            2-tuple of the form (IP, Port), which represents the address of the associated supporter
        '''
        return self._addr
        
    def get_min_peer(self):
        '''@return:
            The amount of peers that are needed at minimum to activate the associated supporter
        '''
        return self._min_peer
    
    def get_max_peer(self):
        '''@return:
            The amount of peers that the supporter is able to supply at maximum
        '''
        return self._max_peer

    def add_supported_peer(self, monitored_peer):
        '''Adds a given MonitoredPeer to the internal list of supported peers. Please be aware
        that this method does not check if the addition of the given peer results in an amount
        of peers larger than the supporter can supply. Such checks have to be performed at the
        caller.
        
        @param monitored_peer:
            Instance of MonitoredPeer that shall be added to the list of currently supported peers
                                    
        @return:
            NoneType
        '''
        # TODO (mgu): Should probably raise an error if someone wants to insert more peers than possible
        # TODO (mgu): Should probably raise an error if the given peer is not in StarvingState
        assert monitored_peer is not None
        if monitored_peer not in self._supported_peers:
            self._updated = True
            self._supported_peers.append(monitored_peer)
            
    def cancel_support_for_all_peers(self):
        '''Removes all supported peers from the supporter and resets them to STARVING state.
        
        @return:
            NoneType
        '''
        # ugly, but a quick hack in order to avoid concurrency issues
        # TODO (mgu): use deepcopy of the list here
        collected_peers = []
        for mp in self._supported_peers:
            collected_peers.append(mp)
        for mp in collected_peers:
            self.remove_supported_peer(mp)
            mp.support_aborted()
            
    def remove_supported_peer(self, monitored_peer):
        '''Removes a MonitoredPeer from the list of supported ones.
        
        @param monitored_peer:
            Instance of MonitoredPeer that shall be removed from the list of currently supported
            peers
                                    
        @return:
            NoneType
        '''
        # TODO (mgu): Should probably check if the given monitored peer is in an applicable state
        assert monitored_peer is not None
        if monitored_peer in self._supported_peers:
            self._supported_peers.remove(monitored_peer)
            self._updated = True
            
    def available_slots(self):
        '''@return:
            The amount of currently available slots at the associated supporter.
        '''
        return self.get_max_peer() - len(self._supported_peers)
    
    def assigned_slots(self):
        '''@return:
            The amount of currently assigned slots at the associated supporter.
        '''
        return len(self._supported_peers)
    
    def minimum_starving_peers_reached(self):
        '''@return:
            Boolean value, indicating whether the supporter has reached its minimum amount
        '''
        # TODO (mgu): Is this method called somewhere?
        return len(self._supported_peers) - self.get_min_peer() >= 0
    
    def reset_update_counter(self):
        #print>>sys.stderr.write("Old state: %s\n" % self._updated)
        value = self._updated
        self._updated = False
        return value
    
    def get_supported_peers(self):
        '''@return:
            List of MonitoredPeers instances that are currently assigned to the associated
            supporter.
        '''
        return self._supported_peers
    
    def update_supported_peer_list(self):
        '''Performs an update of the supportee list. Removes every peer that is in default state.
        Please note that the default state is the only state reachable from the supported state.
        Thus, it is not necessary to check for other states.
        
        @return:
            NoneType
        '''
        to_be_removed = []
        for peer in self.get_supported_peers():
            if isinstance(peer.get_state(), DefaultState):
                to_be_removed.append(peer)
        for peer in to_be_removed:
            self.remove_supported_peer(peer)
            self._updated = True

#___________________________________________________________________________________________________
            
class SupporterMonitor(object):
    '''This class keeps track of all registered peers and supporters and handles incoming messages.
    State transitions for peers are triggered synchronously in the resp. MonitoredPeer instances
    upon the receipt of a peer message. SupporterMonitor also triggers state changes for peers
    as well as supporters asynchronously by calling its update method in regular intervals of
    1 second.
    '''
    def __init__(self):
        self._logger = logging.getLogger("Tracker.SupporterMonitor")
        self._dispatcher = SupporteeListDispatcher(self)
        self._monitored_peers = []
        self._monitored_supporters = []
        self._active_supporters = []
        self._lock = threading.Lock()
        self.schedule_next_asynchronous_update()
        # FIXME: pass it to states differently ...
        # TODO: underneath two lines should be obsolete!
        #global monitored_peers
        #monitored_peers = self._monitored_peers
        
        # contains supporter servers that were marked as dead (last communication was not
        # successful) and should be removed in the next update cycle (we cant do this
        # directly because of concurrency issues)
        self._dead_supporters = []
        
    def schedule_next_asynchronous_update(self):
        '''Schedules the next asynchronous state update for peers and supporters.
        
        @return:
            NoneType
        '''
        for th in threading.enumerate():
            if th.getName() == "MainThread" and not th.isAlive():
                return
        
        t = threading.Timer(1.0, self.update_states)
        t.start()
        
    def get_monitored_peers(self):
        '''@return:
            List containing MonitoredPeer instances
        '''
        return self._monitored_peers
    
    def get_monitored_supporters(self):
        '''@return:
            List containing all MonitoredSupporter instances, independent of their state
            (active, not active)
        '''
        return self._monitored_supporters
    
    def get_active_supporters(self):
        '''@return:
            List containing all MonitoredSupporter instances that reside in the ACTIVE state
        '''
        return self._active_supporters
        
    def register_monitored_peer(self, id, ip, port, peer_type):
        '''Registers a peer at the monitor.
        
        @param id:
            ID of the peer to be registered
        @param ip:
            IP address of the peer
        @param port:
            port address of the peer
        @param peer_type:
            status of the peer (leecher or seeder)
        
        @return:
            The newly created MonitoredPeer instance. NoneType, if a MonitoredPeer instance
            with the given attributes already exists.
        '''
        self._lock.acquire()
        
        mp = MonitoredPeer(id, ip, port, peer_type)
        if mp not in self._monitored_peers:
            self._monitored_peers.append(mp)
        else:
            mp = None
            
        self._lock.release()
        
        self.received_peer_message(MSG_PEER_REGISTERED, id)
        
        return mp
    
    def unregister_monitored_peer(self, monitored_peer):
        '''Unregisters a previously registered peer from the monitor.
        
        @param monitored_peer:
            Instance of MonitoredPeer that shall be unregistered from the monitor
            
        @return:
            NoneType
        '''
        assert monitored_peer is not None
        assert isinstance(monitored_peer, MonitoredPeer)
        
        if monitored_peer in self._monitored_peers:
            self._monitored_peers.remove(monitored_peer)
            
    def register_monitored_supporter(self, id, addr, min_peer, max_peer):
        '''Registers a supporter server at the monitor.
        
        @param id:
            ID of the supporter to be registered
        @param addr:
            2-tuple of the form (IP address, port address)
        @param min_peer:
            Minimum number of supportees that have to be assigned to this supporter
            in order to activate it
        @param max_peer:
            Maximum number of supportees that can be assigned to this supporter
            
        @return:
            The newly created MonitoredSupporter instance. NoneType, if a MonitoredSupporter
            with the given attributes already exists.
        '''
        self._lock.acquire()
        
        ms = MonitoredSupporter(id, addr, min_peer, max_peer)
        if ms not in self._monitored_supporters:
            self._monitored_supporters.append(ms)
            self._dispatcher.register_proxy(ms)
        else:
            ms = None
        
        self._lock.release()
        
        return ms
            
    def unregister_monitored_supporter(self, monitored_supporter):
        '''Unregisters a previously registered supporter from the monitor.
        
        @param monitored_supporter:
            Instance of MonitoredSupporter that shall be unregistered from the monitor
                                         
        @return:
            NoneType
        '''
        assert monitored_supporter is not None
        assert isinstance(monitored_supporter, MonitoredSupporter)

        if monitored_supporter in self._monitored_supporters:
            monitored_supporter.cancel_support_for_all_peers()
            self._monitored_supporters.remove(monitored_supporter)
            self._dispatcher.unregister_proxy(monitored_supporter)
            
    def order_active_supporters(self):
        '''Orders all active supporters by decreasing value of their available slots.
        
        @return:
            NoneType
        '''
        tmp = [ (s,s.available_slots()) for s in self._active_supporters]
        tmp.sort(lambda x,y: cmp(y[1],x[1]))
        self._active_supporters = [ s[0] for s in tmp ]
        
    def filter_peers_by_state(self, state_class):
        '''Extracts peers with the given state from the list of all registered peers.
        
        @param state_class:
            Subclass of SupporterMonitor.State which represents the state
            for which we want to filter.
        
        @return:
            List of registered monitored peers that currently reside in the given state
        '''
        return [mp for mp in self._monitored_peers if isinstance(mp.get_state(), state_class)]
    
    def remaining_active_supporters_with_capacity(self):
        '''@return:
            Boolean value, indicating whether we have at least one active supporter that still
            has available slots
        '''
        return len(self._active_supporters) != 0 and self._active_supporters[0].available_slots() > 0
    
    def update_states(self):
        '''Performs an asynchronous state update of all registered monitored peers and supporters.
        The method looks for starving peers and tries to assign them to active supporters. If
        starving peers remain afterwards, it tries to activate new supporters in order to support
        those starving peers. Dispatches supportee lists to all active supporters at the end
        of the state update.
        
        @return:
            NoneType
        '''
        self._lock.acquire()
        self._remove_timedout_peers()
        self._mark_dead_supporters()
        self._remove_dead_supporters()
        
        self._enforce_update_of_monitored_peers()
        self._enforce_update_of_monitored_supporters()

        self._assign_starving_peers_to_active_supporters()
        # at this point, we still might have some starving peers left, but no active
        # servers with free capacities. but we can see if we are able to activate more
        # supporters.
        self._check_for_activation_of_new_supporters()
        # now send new peer_lists to supporters
        self._dispatcher.dispatch_peer_lists()
        self._lock.release()
        self.schedule_next_asynchronous_update()
        
    def _remove_timedout_peers(self):
        '''Removes peers for which the last activity was reported more than PEER_REMOVAL_TIME
        seconds ago.
        
        @return:
            NoneType
        '''
        peers_to_be_removed = []
        ts = time.time()
        for mp in self.get_monitored_peers():
            if (ts - mp.get_ts_last_message()) >= PEER_REMOVAL_TIME:
                peers_to_be_removed.append(mp)
        for mp in peers_to_be_removed:
            self.unregister_monitored_peer(mp)
            
    def _mark_dead_supporters(self):
        '''Tries to contact every registered supporters and marks those that do not respond
        as being dead.
        
        @return:
            NoneType
        '''
        self._dispatcher.query_all_supporters()
            
    def _remove_dead_supporters(self):
        '''Removes supporters that were marked as being dead.
        
        @return:
            NoneType
        '''
        for supporter in self._dead_supporters:
            self.unregister_monitored_supporter(supporter)
        
    def _enforce_update_of_monitored_peers(self):
        '''Triggers an update on all registered monitored peers. This has to be done since
        peer status transitions might happen asynchronously (after a timer runs out).
        
        @return:
            NoneType
        '''
        for mp in self.get_monitored_peers():
            # TODO (mgu): Is the first condition needed any longer? The former code
            # here did not work (removal of the peer) because we have a side-effect if we try
            # to remove an item from a list that is being iterated over.
            if mp.get_ts_last_request() and (time.time() - mp.get_ts_last_request() > 10):
                mp.set_state(DefaultState(mp))
            else:
                mp.get_state().transition()
            
    def _enforce_update_of_monitored_supporters(self):
        '''Triggers an update on all registered supporters. This includes the potential transition
        from ACTIVE to INACTIVE for a specific supporter. Updates the active supporter list.
        
        @return:
            NoneType
        '''
        # check for all supporters if they have peers in their supported list
        # that no longer need support (state == DEFAULT)
        supporters_to_be_inactivated = []
        for supporter in self._active_supporters:
            supporter.update_supported_peer_list()
            if supporter.assigned_slots() == 0:
                supporters_to_be_inactivated.append(supporter)
        self._active_supporters = [s for s in self._active_supporters if s not in supporters_to_be_inactivated]

    def _assign_starving_peers_to_active_supporters(self):
        '''Tries to assign starving peers to already active supporters. This method relies on the
        available slots of all currently active supporters, which means that it can fail to 
        allocate slots for all starving peers.
        
        @return:
            NoneType
        '''
        starving_peers = self.filter_peers_by_state(StarvingState)
        
        while len(starving_peers) > 0:
            peer = starving_peers[0]
            # 2. do we have active servers with free slots? it suffices to look
            # at the first supporter of the active list, since we keep this list
            # ordered
            active_supporters = self.get_active_supporters()
            
            if self.remaining_active_supporters_with_capacity():
                # assign peer to supporter and re-order the active list 
                self.assign_peer_to_supporter(peer, active_supporters[0])
                starving_peers.remove(peer)
                self.order_active_supporters()
            else:
                
                # this is the case if we have no longer any active supporters that
                # can provide slots to suffering peers. we break in this case and
                # handle the set of remaining peers (starving_peers) next
                break
    
    def _check_for_activation_of_new_supporters(self):
        '''Checks if we can activate new supporters in order to support remaining starving peers
        (that could not be assigned to a supporter during the current update phase).
        
        @return:
            NoneType
        '''
        def sorted_list_of_inactive_supporters():
            # create a list with supporters that are inactive and sort this list
            # in ascending order of min_peers, since we want to help suffering
            # peers as fast as possible (but please consider the fact this will
            # not result in an optimal distribution of starving peers in combination
            # with the used assignment algorithm underneath
            inactive_supporters = [(s,s.get_min_peer()) for s in self._monitored_supporters if s not in self._active_supporters]
            if len(inactive_supporters) == 0:
                return []
            inactive_supporters.sort(lambda x,y: cmp(x[1],y[1]))
            return inactive_supporters
        
        def retrieve_activation_index(starving_peers, inactive_supporters):
            # checks how many supporters (up to some index i) should be activated in order
            # to supply data to starving peers. this algorithm is quite simple. actually, we have a 
            # bin packing problem here at hand which we dont solve optimally using this algorithm.
            # the method used here is a very simple greedy approach, which might not assign peers 
            # optimally, meaning that some peers might remain in the STARVING state, although we 
            # could obtain a better result if our algorithm was better.
            starving_number = len(starving_peers)
            activate_up_to_index = -1
            for i in xrange(len(inactive_supporters)):
                if starving_number >= inactive_supporters[i][1]:
                    starving_number -= inactive_supporters[i][0].available_slots()
                    activate_up_to_index = i
                else:
                    break
            return activate_up_to_index
        
        def activate_supporters_and_assign_peers(index, starving_peers):
            # activates new supporters from the sorted inactivate supporters list starting from
            # index 0 up to the given max. index. the method assigns starving peers on-the-fly
            # to freshly activated supporters.
            if activate_up_to_index >= 0:
                for i in xrange(0,activate_up_to_index+1): # bound for xrange has to be +1
                    self.activate_supporter(inactive_supporters[i][0])
                    assigned_peers = []
                    for peer in starving_peers:
                        self.assign_peer_to_supporter(peer, inactive_supporters[0][0])
                        assigned_peers.append(peer)
                        if inactive_supporters[0][0].available_slots() == 0:
                            break
                    starving_peers = [p for p in starving_peers if p not in assigned_peers]
                # we activated some new supporters and have to maintain their sorting order now
                self.order_active_supporters()
        
        starving_peers = self.filter_peers_by_state(StarvingState)
        inactive_supporters = sorted_list_of_inactive_supporters()
        activate_up_to_index = retrieve_activation_index(starving_peers, inactive_supporters)
        activate_supporters_and_assign_peers(activate_up_to_index, starving_peers)

    def activate_supporter(self, monitored_supporter):
        '''Activates the given MonitoredSupporter.
        
        @param monitored_supporter:
            Instance of MonitoredSupporter which represents the
            supporter that shall transition from INACTIVE to ACTIVE
                                         
        @return:
            NoneType
        '''
        assert monitored_supporter is not None
        assert isinstance(monitored_supporter, MonitoredSupporter)
        
        if monitored_supporter.assigned_slots() != 0:
            # already activated
            return
        
        self._active_supporters.append(monitored_supporter)
        
    def inactivate_supporter(self, monitored_supporter):
        '''Inactivates the given MonitoredSupporter if no peer is currently assigned to it.
        
        @param monitored_supporter:
            Instance of MonitoredSupporter which represents the
            supporter that shall transition from ACTIVE to INACTIVE
                                         
        @return:
            NoneType
        '''
        assert monitored_supporter is not None
        assert isinstance(monitored_supporter, MonitoredSupporter)
        
        if monitored_supporter.assigned_slots() == 0:
            self._active_supporters.remove(monitored_supporter)
            
    def assign_peer_to_supporter(self, monitored_peer, monitored_supporter):
        '''Assigns a peer to an active supporter and triggers the update of the peer's state.
        
        @param monitored_peer:
            Instance of MonitoredPeer which represents the peer that
            will be supported by the given MonitoredSupporter
        @param monitored_supporter:
            Instance of MonitoredSupporter which represents the supporter
            to which the given MonitoredPeer shall be assigned
                                     
        @return:
            NoneType
        '''
        assert monitored_peer is not None
        assert monitored_supporter is not None
        
        if monitored_supporter not in self._active_supporters:
            return
        
        monitored_supporter.add_supported_peer(monitored_peer)
        self.order_active_supporters()
        monitored_peer.receive_msg(MSG_PEER_SUPPORTED)
        
    def received_peer_message(self, msg_type, peer_id):
        '''Handler method for incoming peer messages. Dispatches the message to the resp.
        monitored peer.
        
        @param msg_type:
            Represents the type of the message
        @param peer_id:
            The ID of the peer that sent the original message
            
        @return:
            NoneType
        '''
        self._lock.acquire()
        found = False
        try:
            for peer in self.get_monitored_peers():
                if peer_id == peer.get_id():
                    self._logger.debug("Dispatching %s message to %s" % (msg_type, peer_id))
                    peer.receive_msg(msg_type)
                    found = True
                    break
            if not found:
                self._logger.warning("Got an unregistered peer ID: %s" % peer_id)
        finally:
            self._lock.release()
            
#___________________________________________________________________________________________________

class SupporteeListDispatcher(object):
    '''This class implements a strategy to dispatch supportee lists to specific supporter
    servers. The communication runs over XML-RPC. The implementation requires the establishment
    of a proxy for every registered supporter.
    '''
    def __init__(self, monitor):
        assert isinstance(monitor, SupporterMonitor)
        
        self._monitor = monitor
        self._logger = logging.getLogger("Tracker.SupporterMonitor.XMLRPC")
        # mapping: hash(MonitoredSupporter) => XML/RPC proxy for that supporter
        self._proxies = {}
        
    def register_proxy(self, supporter):
        '''Creates a proxy for the given supporter.
        
        @param supporter:
            MonitoredSupporter instance representing the supporter to establish the connection to
        
        @return:
            NoneType
        '''
        assert isinstance(supporter, MonitoredSupporter)
        proxy_uri = "http://%s:%i" % (supporter.get_addr()[0], supporter.get_addr()[1]+1)
        self._proxies[supporter] = xmlrpclib.ServerProxy(proxy_uri)
        
    def unregister_proxy(self, supporter):
        '''Dereferences the proxy for the given supporter (if the proxy was created prior
        by calling SupporteeListDispatcher.register_proxy).
        
        @param supporter:
            MonitoredSupporter instance representing the supporter for which the proxy
            shall be terminated
        
        @return:
            NoneType
        '''
        assert isinstance(supporter, MonitoredSupporter)
        if self._proxies.has_key(supporter):
            self._proxies[supporter] = None
            del self._proxies[supporter]
            
    def query_all_supporters(self):
        '''Queries all registered supporters in order to check if they are still alive. If a
        supporter is considered as being dead, it will be marked for removal from the
        supporter monitor.
        
        @return:
            NoneType
        '''
        for supporter in self._monitor.get_monitored_supporters():
            proxy = self._proxies[supporter]
            try:
                proxy.is_alive()
            except:
                self._logger.info("Supporter at %s:%s is not responding. Marking it for unregistering.")
                self._monitor._dead_supporters.append(supporter)
    
    def dispatch_peer_lists(self):
        '''Collects supportee data for every monitored supporter and dispatches the resulting
        supportee lists via the XML-RPC proxy interface to the resp. supporter.
        
        @return:
            NoneType
        '''
        for supporter in self._monitor.get_monitored_supporters():
            # TODO (mgu): The method name suggests that it only resets some values, not returns
            # a truth value. This should be changed! (avoid side-effects or misleading method
            # names)
            if not supporter.reset_update_counter():
                continue # NO CHANGES!
            # gather peers
            peers_to_be_unchoked = []
            for peer in supporter.get_supported_peers():
                peers_to_be_unchoked.append((peer.get_id(), peer.get_ip(), peer.get_port()))
                
            if supporter in self._proxies.keys():
                proxy = self._proxies[supporter]
                # send peer list to resp. supporter
                try:
                    proxy.receive_peer_list(peers_to_be_unchoked)
                    sys.stderr.write("Let supporter %s support peers %s\n" % (supporter.get_addr(), peers_to_be_unchoked))
                except:
                    sys.stderr.write("Failed to connect to supporter %s:%i\n" % (supporter.get_addr()[0], supporter.get_addr()[1]))
            
#___________________________________________________________________________________________________
            
class MonitorState(object):
    '''The MonitorState class provides static methods for summarizing the current state of
    a SupporterMonitor object. The generated output follows the HTML format and gives information
    on monitored peers (current state, address, ...) as well as monitored supporters (assigned
    supportees, ...).
    '''
    def __init__(self):
        pass
    
    def _monitored_peers_to_html(monitor):
        '''Static method which generates HTML-formatted information on the state of all
        peers a SupporterMonitor currently watches.
                
        @param monitor:
            Represents the instance of SupporterMonitor for which the state summary shall be
            generated
            
        @return:
            HTML representation containing state information on all peers that are currently 
            watched by the given SupporterMonitor instance
        '''
        monitored_peers = monitor.get_monitored_peers()
                
        html_string = '<h3>Monitored Peers</h3>\n'
        
        if len(monitored_peers) == 0:
            html_string += 'Nothing to report yet.\n'
        else:
            
            html_string += '<table border=1 cellspacing=1>\n'
            html_string += '<tr><th>ID</th><th>Address</th><th>Current State</th><th>Last received message</th><th># Support Requests</th></tr>\n'
            for peer in monitor.get_monitored_peers():
                html_string += '<tr>\n'
                html_string += '<td>%s</td>' % peer.get_id()
                html_string += '<td>%s:%i</td>' % (peer.get_ip(), peer.get_port())
                html_string += '<td>%s</td>' % str(peer.get_state())
                html_string += '<td>%s</td>' % peer.get_last_received_msg()
                html_string += '<td>%i</td>' % peer.get_number_of_support_requests()
                html_string += '</tr>\n'
            html_string += '<table>\n'
    
        return html_string
    
    _monitored_peers_to_html = staticmethod(_monitored_peers_to_html)
    
    def _monitored_supporters_to_html(monitor):
        '''Static method which generates HTML-formatted output on the state of all supporter
        servers a SupporterMonitor currently watches.
        
        @param monitor:
            Represents the instance of SupporterMonitor for which the state summary shall be
            generated
        
        @return:
            HTML representation containing state information on all supporter servers that the
            given SupporterMonitor instance currently watches
        '''
        monitored_supporters = monitor.get_monitored_supporters()
        
        html_string = '<h3>Monitored Supporters</h3>\n'
        
        if len(monitored_supporters) == 0:
            html_string += 'Nothing to report yet.\n'
        else:
        
            html_string += '<table border=1 cellspacing=1>\n'
            html_string += '<tr><th>ID</th><th>Address</th><th># Supportees</th><th># Slots Available</th></tr>\n'
            for supporter in monitor.get_monitored_supporters():
                html_string += '<tr>\n'
                html_string += '<td>%s</td>' % str(supporter.get_id())
                html_string += '<td>%s</td>' % str(supporter.get_addr())
                html_string += '<td>%i</td>' % supporter.assigned_slots()
                html_string += '<td>%i</td>' % supporter.available_slots()
                html_string += '</tr>\n'
            html_string += '</table>\n'
        
        return html_string

    _monitored_supporters_to_html = staticmethod(_monitored_supporters_to_html)
    
    def retrieve_monitor_state_as_html(monitor):
        '''Static method which generates HTML-formatted output on the current state of all
        watched peers and supporters of the given SupporterMonitor instance. This method
        synchronizes against the SupporterMonitor instance and can thus be called by
        client code in a thread-safe manner.
        
        @param monitor:
            Represents the instance of SupporterMonitor for which the
            state summary shall be generated
        
        @return:
            HTML representation of the above mentioned state information
        '''
        assert isinstance(monitor, SupporterMonitor)
        
        monitor._lock.acquire()

        html_string = '<h2>Supporter Monitor State</h2>\n'
        html_string += MonitorState._monitored_peers_to_html(monitor)
        html_string += MonitorState._monitored_supporters_to_html(monitor)
        
        monitor._lock.release()
        
        return html_string
        
    retrieve_monitor_state_as_html = staticmethod(retrieve_monitor_state_as_html)
