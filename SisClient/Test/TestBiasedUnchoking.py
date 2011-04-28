#!/usr/bin/env python

import sys,time
#,os
from SisClient.PeerSelection import BiasedUnchoking
import unittest
import traceback
import logging
#from SisClient.RankingPolicy.Communicator import Communicator
from SisClient.RankingPolicy import RankingPolicy

SIS_URL="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"

class DummyConnection:
    def __init__(self, ip):
        assert ip<>None
        self.ip = ip
    
    def get_ip(self):
        return self.ip
    
    def __str__(self):
        return "DC(%s)" % self.ip
    
    def __repr__(self):
        return "DC(%s)" % self.ip
    
    def __eq__(self, other):
        return self.ip == other.ip

class TestBiasedUnchoking(unittest.TestCase):

    def testNone(self):
        
        mech = BiasedUnchoking.NoFiltering()
        connections = [DummyConnection('209.34.91.45'), DummyConnection('209.34.91.46'), DummyConnection('209.34.91.47')]
        self.assertEquals(connections, mech.selectConnections(connections, number=-1))        
    
    def testSameIPRanking(self):
        mech = BiasedUnchoking.SISFiltering(RankingPolicy.SameHostPolicy())
        
        connections = [DummyConnection('209.34.91.45')]
        self.assertEquals(connections, mech.selectConnections(connections, number=-1))
        
        connections = [DummyConnection('209.34.91.45'), DummyConnection('127.0.0.1')]
        ref = [DummyConnection('127.0.0.1'), DummyConnection('209.34.91.45')]
        self.assertEquals(ref, mech.selectConnections(connections, number=-1))
        
        connections = [DummyConnection('209.34.91.45'), DummyConnection('209.34.91.46'), DummyConnection('209.34.91.47'), DummyConnection('127.0.0.1')]
        ref = [DummyConnection('127.0.0.1'), DummyConnection('209.34.91.45')]
        # enough numbers
        self.assertEquals(ref, mech.selectConnections(connections, number=2))
        
    def testOddEvenRanking(self):
        mech = BiasedUnchoking.SISFiltering(RankingPolicy.OddEvenPolicy())
        
        connections = [DummyConnection('209.34.91.45')]
        self.assertEquals(connections, mech.selectConnections(connections, number=-1))
        
        connections = [DummyConnection('209.34.91.45'), DummyConnection('209.34.91.46')]
        ref = [DummyConnection('209.34.91.46'), DummyConnection('209.34.91.45')]
        self.assertEquals(ref, mech.selectConnections(connections, number=-1))
        
        connections = [DummyConnection('209.34.91.45'), DummyConnection('209.34.91.46'), DummyConnection('209.34.91.47'), DummyConnection('209.34.91.48')]
        ref = [DummyConnection('209.34.91.46'), DummyConnection('209.34.91.48')]
        # enough numbers
        self.assertEquals(ref, mech.selectConnections(connections, number=2))
        

    def setUp(self):
        pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)

    if len(sys.argv)==2:        
        SIS_URL=sys.argv[1]

    suite = unittest.TestLoader().loadTestsFromTestCase(TestBiasedUnchoking)
    
    unittest.TextTestRunner(verbosity=2).run(suite)