# Written by Bram Cohen, Pawel Garbacki, Boxun Zhang
# see LICENSE.txt for license information

from random import randrange, shuffle
import sys

from BaseLib.Core.BitTornado.clock import clock

try:
    True
except:
    True = 1
    False = 0

DEBUG = False

# _smoothit
import logging
from SisClient.PeerSelection import BiasedUnchoking
# _smoothit

class Choker:
    def __init__(self, config, schedule, picker, seeding_selector, done = lambda: False):
        self.config = config
        self.round_robin_period = config['round_robin_period']
        self.schedule = schedule
        self.picker = picker
        self.connections = []
        self.last_preferred = 0
        self.last_round_robin = clock()
        self.done = done
        self.super_seed = False
        self.paused = False
        schedule(self._round_robin, 5)
        
        # SelectiveSeeding
        self.seeding_manager = None
        
        # _smoothit
        self.biasedUnchoking = BiasedUnchoking.getInstance()
        self._is_supporter_server = False   # for supporter
        self._supportee_list = []           # for supporter
        # TODO: unify usage of IDs via the StaticConfig
        #SmoothIT_
        self.logger = logging.getLogger("Tribler.Choker")
        # _smoothit
        
    def set_supporter_server(self, is_supporter_server):
        self._is_supporter_server = is_supporter_server
        
    def set_round_robin_period(self, x):
        self.round_robin_period = x

    def _round_robin(self):
        self.schedule(self._round_robin, 5)
        if self.super_seed:
            cons = range(len(self.connections))
            to_close = []
            count = self.config['min_uploads']-self.last_preferred
            if count > 0:   # optimization
                shuffle(cons)
            for c in cons:
                # SelectiveSeeding
                if self.seeding_manager is None or self.seeding_manager.is_conn_eligible(c):

                    i = self.picker.next_have(self.connections[c], count > 0)
                    if i is None:
                        continue
                    if i < 0:
                        to_close.append(self.connections[c])
                        continue
                    self.connections[c].send_have(i)
                    count -= 1
                else:
                    # Drop non-eligible connections 
                    to_close.append(self.connections[c])
            for c in to_close:
                c.close()
        if self.last_round_robin + self.round_robin_period < clock():
            self.last_round_robin = clock()
            for i in xrange(1, len(self.connections)):
                c = self.connections[i]
                
                # SelectiveSeeding
                if self.seeding_manager is None or self.seeding_manager.is_conn_eligible(c):
                    u = c.get_upload()
                    if u.is_choked() and u.is_interested():
                        self.connections = self.connections[i:] + self.connections[:i]
                        break
        self._rechoke()

    def _rechoke(self):
        # 2fast
        helper = self.picker.helper
        if helper is not None and helper.coordinator is None and helper.is_complete():
            for c in self.connections:
                if not c.connection.is_coordinator_con():
                    u = c.get_upload()
                    u.choke()
            return

        if self.paused:
            for c in self.connections:
                c.get_upload().choke()
            return

        # NETWORK AWARE
        if 'unchoke_bias_for_internal' in self.config:
            checkinternalbias = self.config['unchoke_bias_for_internal']
        else:
            checkinternalbias = 0

        if DEBUG:
            print >>sys.stderr,"choker: _rechoke: checkinternalbias",checkinternalbias
            
        # 0. Construct candidate list
        preferred = []
        maxuploads = self.config['max_uploads']
        
        # _smoothit
        minuploads = self.config['min_uploads']
        if len(self.connections) == 0:
            return
        self.logger.info("MAXUPLOADS = %d, minUploads = %d, CONNECTIONS=%d" % (maxuploads, minuploads, len(self.connections)))
        # _smoothit
        
        if maxuploads > 1:
            
            # 1. Get some regular candidates
            for c in self.connections:

                # g2g: unchoke some g2g peers later
                if c.use_g2g:
                    continue

                # SelectiveSeeding
                if self.seeding_manager is None or self.seeding_manager.is_conn_eligible(c):
                    u = c.get_upload()
                    if not u.is_interested():
                        continue
                    if self.done():
                        r = u.get_rate()
                    else:
                        d = c.get_download()
                        r = d.get_rate()
                        if r < 1000 or d.is_snubbed():
                            continue
                       
                    # NETWORK AWARENESS 
                    if checkinternalbias and c.na_get_address_distance() == 0:
                        r += checkinternalbias
                        if DEBUG:
                            print >>sys.stderr,"choker: _rechoke: BIASING",c.get_ip(),c.get_port()

                    preferred.append((-r, c))
                    
            self.last_preferred = len(preferred)
            preferred.sort()
            del preferred[maxuploads-1:]
            
            # _smoothit
            self.logger.debug("NORMAL UNCHOKE "+str(preferred))
            # _smoothit
            
            preferred = [x[1] for x in preferred]

            # 2. Get some g2g candidates 
            g2g_preferred = []
            for c in self.connections:
                if not c.use_g2g:
                    continue

                # SelectiveSeeding
                if self.seeding_manager is None or self.seeding_manager.is_conn_eligible(c):

                    u = c.get_upload()
                    if not u.is_interested():
                        continue
    
                    r = c.g2g_score()
                    if checkinternalbias and c.na_get_address_distance() == 0:
                        r[0] += checkinternalbias
                        r[1] += checkinternalbias
                        if DEBUG:
                            print >>sys.stderr,"choker: _rechoke: G2G BIASING",c.get_ip(),c.get_port()
                   
                    g2g_preferred.append((-r[0], -r[1], c))
                    
            g2g_preferred.sort()
            del g2g_preferred[maxuploads-1:]
            
            # _smoothit
            self.logger.debug("G2G UNCHOKE "+str(g2g_preferred))
            # _smoothit

            g2g_preferred = [x[2] for x in g2g_preferred]

            preferred += g2g_preferred


        # 
        count = len(preferred)
        hit = False
        to_unchoke = []
        to_choke = [] # smoothit
        # 3. The live source must always unchoke its auxiliary seeders
        # LIVESOURCE
        if 'live_aux_seeders' in self.config:
            
            for hostport in self.config['live_aux_seeders']:
                for c in self.connections:
                    if c.get_ip() == hostport[0]:
                        u = c.get_upload()
                        to_unchoke.append(u)

                        # _smoothit
                        self.logger.info("Choker: _rechoke: LIVE: Permanently unchoking aux seed",hostport)
                        # _smoothit
                        
                        #print >>sys.stderr,"Choker: _rechoke: LIVE: Permanently unchoking aux seed",hostport

        # 4. Select from candidate lists, aux seeders always selected
        
        # _smoothit
        # old: for c in self.connections:
#        print >>sys.stderr, "Is supporter server %s" % self._is_supporter_server
        
        if not self._is_supporter_server:
            # if the peer is a regular client and not a supporter server, we use the following
            # code to select unchoke candidates
            sis_sorted = self.sort_by_locality(self.connections)
            for c in sis_sorted:
                u = c.get_upload()
                if c in preferred:
                    to_unchoke.append(u)
                    self.logger.info("Preferred unchoke: "+str(c))
                else:
                    # TODO: apply service policies to optimistic slot
                    if count < maxuploads or not hit:
                        to_unchoke.append(u)
                        self.logger.debug("Unchoke new peers %s %f  " % (u.get_ip(), u.get_rate()))
                        if u.is_interested():
                            count += 1
                            if not hit:
                                self.logger.info("OPTIMISTIC UNCHOKE: "+str(c))
                            else:
                                self.logger.info("REGULAR UNCHOKE: "+str(c))
                            hit = True
                    else:
                        if not c.connection.is_coordinator_con() and not c.connection.is_helper_con():
                            u.choke()
                        elif u.is_choked():
                            to_unchoke.append(u)
        else:
            # the peer is a supporter server, so we have to select those peers, that
            # were sent from a supporter monitor and choke every other peer
            to_unchoke = []
            to_choke = [] 
            print >>sys.stderr, "Peers to support: %s" % self._supportee_list
            for c in self.connections:
                for peer in self._supportee_list:
                    #ip = peer[1]
                    #port = peer[2]
                    id = peer[0]
                    if id == c.get_id():
                
                        to_unchoke.append(c.get_upload())
                        break
                
            # append every connection that is not in to_unchoke to to_choke
            for c in self.connections:
                if c.get_upload() not in to_unchoke:
                    to_choke.append(c.get_upload())
                    
            
        # _smoothit

        # 5. Unchoke selected candidates
        
        # _smoothit
        to_log = []
        #print >>sys.stderr, "Should support: %s" % (to_unchoke)
        self.logger.info("TO CHOKE : %s " % to_choke)
        for u in to_unchoke:
            u.unchoke()
            to_log.append(u.get_ip())
        self.logger.info("UNCHOKING: " + str(to_log))
        
        if self._is_supporter_server:
            for u in to_choke:
                u.choke() # choke all others
        
        # count interested unchokes!   
        interested = [u for u in to_unchoke if u.is_interested()]
        self.logger.info("INTERESTED UNCHOKE: %d" % len(interested))
        # _smoothit
        
    def sort_by_locality(self, connections):
        ''' SmoothIT based sorting to impose some level of locality. '''
        askSis = list(connections)
        #for c in connections:
        #    u = c.get_upload()
        #    if not u.is_interested():
        #        continue
        #    askSis.append(c)
        #to_unchoke = []
        
        # ask SIS-Server for its ranking, that will be used only for optimistic unchokes)
        #optimisticUnchoke = None
        sisResult = self.biasedUnchoking.selectConnections(askSis)
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Original "+str([x.get_ip() for x in connections]))
            self.logger.info("SIS sorted "+str([x.get_ip() for x in sisResult]))
        assert len(sisResult) == len(connections), "sent %d but received %d " % (len(connections), len(sisResult))
        return sisResult
        # _SmoothIT

    def add_connection(self, connection, p = None):
        """
        Just add a connection, do not start doing anything yet
        Must call "start_connection" later!
        """
        print >>sys.stderr, "Added connection",connection
        if p is None:
            p = randrange(-2, len(self.connections) + 1)
        connection.get_upload().choke()
        self.connections.insert(max(p, 0), connection)
        self.picker.got_peer(connection)
        self._rechoke()
        
    def start_connection(self, connection):
        connection.get_upload().unchoke()
    
    def connection_made(self, connection, p = None):
        if p is None:
            p = randrange(-2, len(self.connections) + 1)
        self.connections.insert(max(p, 0), connection)
        self.picker.got_peer(connection)
        self._rechoke()

    def connection_lost(self, connection): 
        """ connection is a Connecter.Connection """
        # Raynor Vliegendhart, RePEX:
        # The RePEX code can close a connection right after the handshake 
        # but before the Choker has been informed via connection_made. 
        # However, Choker.connection_lost is still called when a connection
        # is closed, so we should check whether Choker knows the connection:
        if connection in self.connections:
            self.connections.remove(connection)
            self.picker.lost_peer(connection)
            if connection.get_upload().is_interested() and not connection.get_upload().is_choked():
                self._rechoke()

    def interested(self, connection):
        if not connection.get_upload().is_choked():
            self._rechoke()

    def not_interested(self, connection):
        if not connection.get_upload().is_choked():
            self._rechoke()

    def set_super_seed(self):
        while self.connections:             # close all connections
            self.connections[0].close()
        self.picker.set_superseed()
        self.super_seed = True

    def pause(self, flag):
        self.paused = flag
        self._rechoke()
    
    # SelectiveSeeding
    def set_seeding_manager(self, manager):
        # When seeding starts, a non-trivial seeding manager will be set
        self.seeding_manager = manager

    def receive_supportee_list(self, supportee_list):
        self._supportee_list = supportee_list