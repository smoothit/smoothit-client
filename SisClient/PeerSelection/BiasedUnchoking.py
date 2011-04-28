# Written by Sebastian Schmidt (TUD)
# see LICENSE.txt for license information
#import sys
#from random import *
#from datetime import *
#from time import *
import logging

#import BaseLib.Core

communicator=None

_instance = None

logger = logging.getLogger('PeerSelection')

def getInstance():
    global _instance
    if _instance is None:
        BiasedUnchoking("none")
    return _instance

#TODO: rename SISFiltering into LocalityAwareness
class BiasedUnchoking(object):
    '''
    Abstract class which provides a method to select connections in dependence of the used mode. The concrete 
    implementation is chosen in dependence of the given booleans.
    The selection can be used for the unchoking-decisions.
    '''
    
    def __init__(self, mode, policy = None):
        global _instance
        
        self._setMode(mode, policy)
        _instance = self
    
    def _setMode(self, mode, policy=None):
    
        if mode=='none' or mode == None:
            self.selection = NoFiltering()                
        elif mode=='enable':
            self.selection = SISFiltering(policy)
        else:
            raise RuntimeError("Unsupported peer selection mode: "+mode)
    
    
    def selectConnections(self, connections, number=-1):
        '''
        Returns a subset of the given connections due to the concrete implementation.
        '''
        return self.selection.selectConnections(connections, number)


# No filtering of connections takes place
class NoFiltering(BiasedUnchoking):
    
    def __init__(self):
        pass
    
    # don't filter peers before unchoking
    def selectConnections(self, connections, number=-1):
        return connections

# Filter locally in dependency of remotely determined preferences
class SISFiltering(BiasedUnchoking):
    
    def __init__(self, policy):
        self.policy = policy
        assert policy
    
    def selectConnections(self, connections, number=-1):
        '''
        Remote filtering: 
        returns number connections or number-1 connections, if there aren't number connections with a rating better than 0
        '''     
        toAsk = []
#        ownIP = 'unknown'
        for c in connections:
#           if ownIP == 'unknown': @IndentOk
#              ownIP = c.get_myip() @IndentOk
            toAsk.append(c.get_ip())
        
        logger.debug("USING REMOTE FILTERING")
        logger.debug("REQUESTED - " + str(toAsk))
        
        rankedIPs = self.policy.getRankedPeers(toAsk)
        
        if rankedIPs is None:
            # Failed to obtain ranking! what to do?
            logger.error("SIS COMMUNICATION FAILED - PROCEED IN NORMAL MODE")
            return connections
        else:
        
            # now sort connections by ratings, highest ratings first
            result = sorted(connections, key = lambda con: rankedIPs[con.get_ip()], reverse= True)
    
            # now strip some values if required
            if number > -1:
                result = result[0: number]

            return result
    