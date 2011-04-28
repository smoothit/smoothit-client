#!/usr/bin/env python

import sys,zlib
import urllib
from SisClient.RankingPolicy.Communicator import Communicator
import unittest
import traceback
import logging
from SisClient.Utils.serialize import serialize

SIS_URL="http://127.0.0.1:8080/sis/monitor"

class TestMonitorReports(unittest.TestCase):

    def testReporting(self):
        test_dict = {'status': '3', 'down_rate': 0.0, 
                     'peers': [{'down_rate': 0.0, 'up_total': 0.0, 'addr': '88.192.42.88:55788:L', 'g2g': 'bt', 'down_str': 'CI', 'down_total': 0.0, 'g2g_score': '0.0,0.0', 'up_rate': 0.0, 'id': '2D5554313832302D7A387857FB8CC1DCF440BA71', 'up_str': 'ciO'}], 'p_played': 0, 'listenport': 17534, 't_stall': 0, 'timestamp': 1247494852.4792919, 'validrange': '(0, 3543)', 't_prebuf': -1, 'filename': 'Big_Buck_Bunny_1080p_surround_frostclick.com_frostwire.com', 'p_dropped': 0, 'live': False, 'pieces': {}, 'peerid': "'R452-----OphdjzOfDnh'", 'up_total': 0.0, 'down_total': 0.0, 'progress': 0.0, 'up_rate': 0.0, 'infohash': "'\\xf8KQ\\xf0\\xd2\\xc3EZ\\xb5\\xda\\xbbfC\\xb44\\x024\\xcd\\x03n'", 'id': 1234567, 'p_late': 0}
        
        #compress = len(sys.argv) > 1 and sys.argv[1]=='compress'
        compress = False
        try:
            data = serialize(test_dict)
            #print "XML",len(data),"\n"#,data
            
            f = open('resources/report.xml', 'w')
            f.write(data)
            f.close()
            
            if compress:
                data = zlib.compress(data, 9 )
#                print "compressed", len(data)
                f =  open('resources/compressed.gz', 'w')
                f.write(data)
                f.close()
#               print "decompressed: ", len(zlib.decompress(data))
            data = data.encode("base64")
            f = open('resources/compressed_and_encoded.b64', 'w')
            f.write(data)
            f.close()
            
            self.assertEqual(1804, len(data), "Wrong encoded size, it was %d" % len(data))
            decoded = data.decode("base64")
            self.assertEqual(1334, len(decoded), "Wrong plain xml size, it was %d " %len(decoded)) 
            
            #test ="eNqVlMGO2jAQhs/wFCsutNIuJLbTeKsUaYEiVa2E2mOFFJnECS6ObTnOLvTp6wClJJgCHIbY+mY84/k9UUHUgyAF/dRTRFNheqNuJ1rT7WGzNMRUZe/BbNVupZnIeyMYDS3SJFP5JmJNDP0LZ1wSG84beA5aUaqPYTkrd+d2OhEztDjspizZ70b/cvQO2F3HNvhKxUYawm/ESZrqdvUYD/xnMEBggPHHIAit/eZ0ZmnbFUyDIEDQhxgC6IFp+AJxiINwNsaTiT+dzBDyxi+h7wyXg7wdb2mc5O5SLNPGJ18u4/fcir3EO67c5h2XidS0nY51ePzPEY4CEjY/0tHQ6mLUjYa1ZkZdK69zmV1N9FSScaqlUvTYNFa/BhdZ65UKJbVpoH4YQOTAja2EcH41rGEFtWShWun6AIXoGeHAag47E+cnNV4Mf135J3DGOK2/2g0YszweV8naGiG2se9hzzaq0lpWIo0zLUuTcJasB4ks9ss3pmm9ct7jazPtGeEldYBMZHJFylU7m/5ik+Gv3631FpsULDYJ/PxzsVkGdkXs/zKbWIvQYuMBa5LUfkDRvzCPzp9r/wcKwFP9m6tV+uv3PJuKldM9Vpxsb5COiZWmyyprgE/+pXl6rWEn05vRhJa76b1/F430tMw1LcubWs+aVfgAouBD6ABfCWepJiI/U8k77/EB2jn3/uC1T+kPxmMD+A=="
            #print "decoded and unzipped: ", zlib.decompress(test.decode("base64"))
        except Exception:
            traceback.print_exc()
            self.fail("Failed to serialize")
        
        try:
            #serverAddress = "http://localhost:8080/sis/monitor"
            sock = urllib.urlopen(SIS_URL, data)
            result = sock.read()
            sock.close()
        except:
            traceback.print_exc()
            self.fail("Failed to send to server at "+SIS_URL)
        
    
        def setUp(self):
            self.rankingSource = Communicator(SIS_URL)
            self.use_simple=True

#TODO: create superclass for SIS related settings
if __name__ == '__main__':
    #unittest.main()
    logging.basicConfig(level=logging.WARNING)
#    global SIS_URL
    if len(sys.argv)==2:        
        SIS_URL=sys.argv[1]

    #print "USE %s as SIS_URL" % SIS_URL
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMonitorReports)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
