# Written by Arno Bakker
# see LICENSE.txt for license information

# TODO: let one hit to SIMPLE+METADATA be P2PURL
import unittest
import os
import sys
import time
from BaseLib.Core.Utilities.Crypto import sha
from types import StringType, DictType, IntType
from M2Crypto import EC

from BaseLib.Test.test_as_server import TestAsServer
from olconn import OLConnection
from BaseLib.Core.API import *
from BaseLib.Core.BitTornado.bencode import bencode,bdecode
from BaseLib.Core.BitTornado.BT1.MessageID import *


DEBUG=True


class TestRemoteQuery(TestAsServer):
    """ 
    Testing QUERY message of Social Network extension V1
    """
    
    def setUpPreSession(self):
        """ override TestAsServer """
        TestAsServer.setUpPreSession(self)
        # Enable remote query
        self.config.set_remote_query(True)
        self.config.set_torrent_collecting_dir(os.path.join(self.config_path, "tmp_torrent_collecting"))

    def setUpPostSession(self):
        """ override TestAsServer """
        TestAsServer.setUpPostSession(self)

        #self.mypermid = str(self.my_keypair.pub().get_der())
        #self.hispermid = str(self.his_keypair.pub().get_der())
        
        self.torrent_db = self.session.open_dbhandler(NTFY_TORRENTS)
        try:
            # Add two torrents that will match our query and one that shouldn't
            self.bmetainfo1 = self.get_default_torrent('sumfilename1','Hallo S01E10')
            dbrec= self.torrent_db.addExternalTorrent('sumfilename1',metadata=self.bmetainfo1)
            self.infohash1 = dbrec['infohash']
            
            self.bmetainfo2 = self.get_default_torrent('sumfilename2','Hallo S02E01')
            dbrec = self.torrent_db.addExternalTorrent('sumfilename2',metadata=self.bmetainfo2)
            self.infohash2 = dbrec['infohash']
    
            self.bmetainfo3 = self.get_default_torrent('sumfilename3','Halo Demo')
            self.torrent_db.addExternalTorrent('sumfilename3',metadata=self.bmetainfo3)
        except:
            print_exc()
        

    def tearDown(self):
        TestAsServer.tearDown(self)
        self.session.close_dbhandler(self.torrent_db)
      

    def get_default_torrent(self,filename,title):
        metainfo = {}
        metainfo['announce'] = 'http://localhost:0/announce'
        metainfo['announce-list'] = []
        metainfo['creation date'] = int(time.time())
        info = {}
        info['name'] = title
        info['length'] = 481
        info['piece length'] = 2 ** 16
        info['pieces'] = '*' * 20
        metainfo['info'] = info
        path = os.path.join(self.config.get_torrent_collecting_dir(),filename)
        tdef = TorrentDef.load_from_dict(metainfo)
        tdef.save(path)
        return bencode(metainfo)

    def test_all(self):
        """ 
            I want to start a Tribler client once and then connect to
            it many times. So there must be only one test method
            to prevent setUp() from creating a new client every time.

            The code is constructed so unittest will show the name of the
            (sub)test where the error occured in the traceback it prints.
        """
        # 1. test good QUERY
        self.subtest_good_simple_query()
        self.subtest_good_simpleplustorrents_query()

        # 2. test various bad QUERY messages
        self.subtest_bad_not_bdecodable()
        self.subtest_bad_not_dict1()
        self.subtest_bad_not_dict2()
        self.subtest_bad_empty_dict()
        self.subtest_bad_wrong_dict_keys()

        self.subtest_bad_q_not_list()
        self.subtest_bad_id_not_str()

    #
    # Good QUERY
    #
    def subtest_good_simple_query(self):
        """ 
            test good QUERY messages: SIMPLE
        """
        print >>sys.stderr,"test: good QUERY SIMPLE"
        s = OLConnection(self.my_keypair,'localhost',self.hisport)
        msg = self.create_good_simple_query()
        s.send(msg)
        resp = s.recv()
        if len(resp) > 0:
            print >>sys.stderr,"test: good QUERY: got",getMessageName(resp[0])
        self.assert_(resp[0] == QUERY_REPLY)
        self.check_rquery_reply("SIMPLE",resp[1:])
        time.sleep(10)
        # the other side should not have closed the connection, as
        # this is all valid, so this should not throw an exception:
        s.send('bla')
        s.close()

    def create_good_simple_query(self):
        d = {}
        d['q'] = 'SIMPLE hallo'
        d['id'] = 'a' * 20
        return self.create_payload(d)


    def subtest_good_simpleplustorrents_query(self):
        """ 
            test good QUERY messages: SIMPLE+METADATA
        """
        print >>sys.stderr,"test: good QUERY SIMPLE+METADATA"
        s = OLConnection(self.my_keypair,'localhost',self.hisport)
        msg = self.create_good_simpleplustorrents_query()
        s.send(msg)
        resp = s.recv()
        if len(resp) > 0:
            print >>sys.stderr,"test: good QUERY: got",getMessageName(resp[0])
        self.assert_(resp[0] == QUERY_REPLY)
        self.check_rquery_reply("SIMPLE+METADATA",resp[1:])
        time.sleep(10)
        # the other side should not have closed the connection, as
        # this is all valid, so this should not throw an exception:
        s.send('bla')
        s.close()

    def create_good_simpleplustorrents_query(self):
        d = {}
        d['q'] = 'SIMPLE+METADATA hallo'
        d['id'] = 'b' * 20
        return self.create_payload(d)



    def create_payload(self,r):
        return QUERY+bencode(r)

    def check_rquery_reply(self,querytype,data):
        d = bdecode(data)
        
        print >>sys.stderr,"test: Got reply",`data`
        
        self.assert_(type(d) == DictType)
        self.assert_(d.has_key('a'))
        self.check_adict(d['a'])
        self.assert_(d.has_key('id'))
        id = d['id']
        self.assert_(type(id) == StringType)

        k = d['a'].keys()
        self.assert_(len(k) == 2)
        var1 = k[0] == (self.infohash1) and k[1] == (self.infohash2)
        var2 = k[0] == (self.infohash2) and k[1] == (self.infohash1)
        self.assert_(var1 or var2)

        # OLPROTO_VER_NINETH must contain torrent_size
        for infohash, torrent in d['a'].iteritems():
            if infohash == self.infohash1:
                self.assert_(torrent['torrent_size'], len(self.bmetainfo1))
            elif infohash == self.infohash2:
                self.assert_(torrent['torrent_size'], len(self.bmetainfo2))
            else:
                self.assertFalse()

            
        if querytype.startswith("SIMPLE+METADATA"):
            for infohash, torrent in d['a'].iteritems():
                self.assert_('metadata' in torrent)
                bmetainfo = torrent['metadata']
                if infohash == self.infohash1:
                    self.assert_(bmetainfo == self.bmetainfo1)
                elif infohash == self.infohash2:
                    self.assert_(bmetainfo == self.bmetainfo2)
                else:
                    self.assertFalse()


    def check_adict(self,d):
        self.assert_(type(d) == DictType)
        for key,value in d.iteritems():
            self.assert_(type(key) == StringType)
            self.assert_(len(key) == 20)
            self.check_rdict(value)
    
    def check_rdict(self,d):
        self.assert_(type(d) == DictType)
        self.assert_('content_name' in d)
        self.assert_(type(d['content_name']) == StringType)
        self.assert_('length' in d)
        self.assert_(type(d['length']) == IntType)
        self.assert_('leecher' in d)
        self.assert_(type(d['leecher']) == IntType)
        self.assert_('seeder' in d)
        self.assert_(type(d['seeder']) == IntType)


    # Bad rquery
    #    
    def subtest_bad_not_bdecodable(self):
        self._test_bad(self.create_not_bdecodable)

    def subtest_bad_not_dict1(self):
        self._test_bad(self.create_not_dict1)

    def subtest_bad_not_dict2(self):
        self._test_bad(self.create_not_dict2)

    def subtest_bad_empty_dict(self):
        self._test_bad(self.create_empty_dict)

    def subtest_bad_wrong_dict_keys(self):
        self._test_bad(self.create_wrong_dict_keys)

    def subtest_bad_q_not_list(self):
        self._test_bad(self.create_bad_q_not_list)

    def subtest_bad_id_not_str(self):
        self._test_bad(self.create_bad_id_not_str)


    def _test_bad(self,gen_rquery_func):
        print >>sys.stderr,"test: bad QUERY",gen_rquery_func
        s = OLConnection(self.my_keypair,'localhost',self.hisport)
        msg = gen_rquery_func()
        s.send(msg)
        time.sleep(5)
        # the other side should not like this and close the connection
        self.assert_(len(s.recv())==0)
        s.close()

    def create_not_bdecodable(self):
        return QUERY+"bla"

    def create_not_dict1(self):
        rquery = 481
        return self.create_payload(rquery)

    def create_not_dict2(self):
        rquery = []
        return self.create_payload(rquery)

    def create_empty_dict(self):
        rquery = {}
        return self.create_payload(rquery)

    def create_wrong_dict_keys(self):
        rquery = {}
        rquery['bla1'] = '\x00\x00\x00\x00\x00\x30\x00\x00'
        rquery['bla2'] = '\x00\x00\x00\x00\x00\x30\x00\x00'
        return self.create_payload(rquery)


    #
    # Bad q
    #
    def create_bad_q_not_list(self):
        rquery = {}
        rquery['q'] = 481
        rquery['id'] = 'a' * 20
        return self.create_payload(rquery)


    #
    # Bad id
    #
    def create_bad_id_not_str(self):
        rquery = {}
        rquery['q'] = ['hallo']
        rquery['id'] = 481
        return self.create_payload(rquery)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRemoteQuery))
    
    return suite

def sign_data(plaintext,keypair):
    digest = sha(plaintext).digest()
    return keypair.sign_dsa_asn1(digest)

def verify_data(plaintext,permid,blob):
    pubkey = EC.pub_key_from_der(permid)
    digest = sha(plaintext).digest()
    return pubkey.verify_dsa_asn1(digest,blob)


if __name__ == "__main__":
    unittest.main()

