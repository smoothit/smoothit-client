from __future__ import with_statement
import unittest
import logging
import subprocess
import os
import urllib
import time

from SisClient.Testbed.Utils.utils import *
from subprocess import Popen

#
#    X  default url and port
#    * custom port
#    * custom url
#    * mailformed custom url
#    * custom url and wrong custom port

tracker_py = "\"" + FileUtils.get_current_script_directory(__file__) + \
    os.path.normcase('/') + ".." + os.path.normcase('/') + "tracker.py\" "


class TrackerTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TrackerTest("testStartExternalTrackerWithDefaultUrlAndPort"))
        suite.addTest(TrackerTest("testStartExternalTrackerWithCustomUrlAndPort"))
        suite.addTest(TrackerTest("testStartExternalTrackerWithMalformedCustomUrl"))
        return suite
    
    def testDefaultUrlAndPort(self):
        global tracker_py
        cmd = "python " + tracker_py + " -i -f files >&2"
        #TODO: update: since we use random ports instead of default ones!
#        tmp = tempfile.TemporaryFile(mode="wr")
#        output = open(tmp)
        
        child = Popen(cmd, shell=True) #, stderr=output)        
        time.sleep(3)
        
        #u = urllib.urlopen("http://localhost:8859/announce")
        #content_size = int(u.headers.getheader('content-length'))
        #self.assertTrue(content_size == 34)
        #self.assertEquals(u.headers.getheader('content-type'), "text/plain")
        cmd = "kill %i" % (child.pid+1)
        p = Popen(cmd, shell=True)
        time.sleep(3)
        
    def testCustomUrlAndPort(self):
        global tracker_py
        cmd = "python " + tracker_py + " -f files -i -u http://localhost:7777/announce"
        child = Popen(cmd, shell=True)
        time.sleep(3)
        u = urllib.urlopen("http://localhost:7777/announce")
        content_size = int(u.headers.getheader('content-length'))
        self.assertTrue(content_size == 34)
        self.assertEquals(u.headers.getheader('content-type'), "text/plain")
        cmd = "kill %i" % (child.pid+1)
        p = Popen(cmd, shell=True)
        time.sleep(5)
        
    def testMalformedCustomUrl(self):
        global tracker_py
        cmd = "python " + tracker_py + " -f files -i -u http://localhost"
        child = Popen(cmd, shell=True)
        # we expect an unclean shutdown, since the parameters are wrong
        self.assertNotEquals(0, child.wait())
    
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    unittest.main()