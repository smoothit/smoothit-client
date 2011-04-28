#!/usr/bin/env python

import sys,time,os
from SisClient.PeerSelection import NeighborSelection
import unittest
import traceback
import logging
from SisClient.RankingPolicy.RankingPolicy import OddEvenPolicy

SIS_URL="http://127.0.0.1:8080/sis/ClientEndpoint?wsdl"

class TestNeighborSelection(unittest.TestCase):

    def testNone(self):
        
        mech = NeighborSelection.NoFiltering()
        assert mech.acceptAsNeighbor(('209.34.91.45', 12345))
        
        iplist = [('209.34.91.45', 123), ('209.34.91.44', 123), ('209.34.91.47', 123), ('81.19.23.42', 123)]
        sorted = mech.selectAsNeighbors(iplist)
        assert iplist == sorted
        
        sorted = mech.selectAsNeighbors(iplist, 3)
        assert iplist[0:3] == sorted, "original %s, \nselected %s" % (str(iplist[0:3]), str(sorted)) 
        
    def testFillUp(self):
        '''
        Check that the locality cut-off for a sorted list works fine!
        '''        
        ns = NeighborSelection.NeighborSelection()        
        
        ranked = range(1,20)
        biased = ns._fillUp(ranked, -1, locality_pref=1)
        assert ranked == biased[0:len(ranked)], "locality_pref = 1, biased="+ biased
        
        # Now test cut-off
        biased = ns._fillUp(ranked, 6, locality_pref=1)
        assert len(biased) == 6, "locality_pref = 1, biased and cut to 6="+ biased
        assert ranked[0:6] == biased, "expect %s result %s" % (ranked[0:6], biased)
        
        ranked = range(1,16)
        biased = ns._fillUp(ranked, -1, locality_pref = 0)
        assert set(ranked) == set(biased), "locality_pref = 0, biased=%s" % biased
        
        ranked = range(0,20)
        biased = ns._fillUp(ranked, -1, locality_pref = 0.25)
        assert len(ranked)==len(biased)
        assert set(ranked[0:5]) == set(biased[0:5]), "locality_pref = 0.25, biased="+ biased #first quarter -> only ranked ranks        
        
    def testOddEvenLocally(self):
        ranking = OddEvenPolicy()
        mech = NeighborSelection.SISFiltering(1.0, ranking)
        self.tryOddEvenMech(mech)
        
    def testMechanismCreation(self):
        self.assertEquals(NeighborSelection.ns_instance(), None)
        
        mech = NeighborSelection.getInstance()
        assert isinstance(NeighborSelection.ns_instance(), NeighborSelection.NoFiltering)
        
        mech2 = NeighborSelection.createMechanism("none")
        assert isinstance(mech2, NeighborSelection.NoFiltering)
        assert mech<>mech2
        assert NeighborSelection.ns_instance() is mech2
        
        local = NeighborSelection.createMechanism("enable", rankingSource = OddEvenPolicy())
        self.assertTrue(isinstance(local, NeighborSelection.SISFiltering))
        self.assertEquals(NeighborSelection.ns_instance(), local)
        
    def tryOddEvenMech(self, mech):
        # try locality of 1
        assert mech.acceptAsNeighbor(('209.34.91.44', 12345))
        assert not mech.acceptAsNeighbor(('209.34.91.45', 12345))#TODO: check applicability!
        
        # select all but in the right order!
        iplist = [('209.34.91.45', 123), ('209.34.91.44', 123), ('209.34.91.47', 123), ('81.19.23.42', 123)]
        filtered = mech.selectAsNeighbors(iplist)
        
        local = set([('209.34.91.44', 123), ('81.19.23.42', 123)])
        remote = set ([('209.34.91.45', 123), ('209.34.91.47', 123)])
        assert local == set(filtered[0:2]), "local is %s but filtered is %s" % (str(local), str(set(filtered[0:2])))
        assert remote == set(filtered[2:4]), "remote is %s but filtered is %s" % (str(remote), str(set(filtered[0:2])))
        
        filtered = mech.selectAsNeighbors(iplist, 2)
        # pick best two which must be local in this case!
        assert set(local) == set(filtered), "original %s, \nselected %s" % (str(local), str(filtered))
        
        # NOW test that we can cut-off remote peers completely!
        mech.exclude_below = 1# cut off those ranked with 0
        filtered = mech.selectAsNeighbors(iplist)
        assert set(local) == set(filtered), "original %s, \nselected %s" % (str(local), str(filtered))
        

    def setUp(self):
        pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    #unittest.main()
    #global SIS_URL
    if len(sys.argv)==2:        
        SIS_URL=sys.argv[1]
    #print "USE %s as SIS_URL" % SIS_URL
    #TODO: uncomment
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNeighborSelection)
    #suite = unittest.TestSuite()
    #suite.addTest(TestNeighborSelection('testFillUp'))
    #suite.addTest(TestNeighborSelection('testOddEvenLocally'))
    #if os.environ.has_key('UNITTEST_VERBOSITY'):
    #    _verbosity = int(os.environ['UNITTEST_VERBOSITY'])
    #else:
    #    _verbosity = 2
    #print "verbosity is ", _verbosity
    unittest.TextTestRunner(verbosity=2).run(suite)