import unittest
import logging
import os
import shutil
import time
import sys

from subprocess import Popen
from SisClient.Testbed.Utils.utils import FileUtils

class TerminationTest(unittest.TestCase):

    DIRECTORY_TRACKER = "test/termination_tracker"
    DIRECTORY_SEEDER = "test/termination_seeder"
    DIRECTORY_LEECHER = "test/termination_leecher"
    
    FILE = FileUtils.get_current_script_directory(__file__) + \
           os.path.normcase('/') + "reports_large.zip"
    FILE_RELATIVE = FileUtils.get_relative_filename(FILE)
    
    _start_tracker = "sh tracker.sh -f " + DIRECTORY_TRACKER + \
                     " -u http://localhost:8859/announce -d " + DIRECTORY_TRACKER
    _start_client = "sh client.sh -d %s %s"
    _cmd_grep_tracker_pid = "ps -AF | grep tracker.sh"
    _cmd_grep_client_pid = "ps -AF | grep client.sh"
        
    def setUp(self):
        os.mkdir(self.DIRECTORY_TRACKER)
        os.mkdir(self.DIRECTORY_SEEDER)
        os.mkdir(self.DIRECTORY_LEECHER)
        
        shutil.copyfile(self.FILE, self.DIRECTORY_TRACKER + \
                        os.path.normcase('/') + self.FILE_RELATIVE)
    
    def tearDown(self):
        FileUtils.remove_directory_recursively(self.DIRECTORY_TRACKER)
        FileUtils.remove_directory_recursively(self.DIRECTORY_LEECHER)
        FileUtils.remove_directory_recursively(self.DIRECTORY_SEEDER)
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TerminationTest("testTerminateAfterDownload"))
        #suite.addTest(TerminationTest("testTerminateAfterPlayback"))
        #suite.addTest(TerminationTest("testTerminateAfterSeeding"))
        return suite
    
    def _copy_files_to_client(self, from_dir, to_dir, is_seeder=False):
        from_files = [ from_dir + os.path.normcase('/') + self.FILE_RELATIVE + constants.TORRENT_DOWNLOAD_EXT ]
        if is_seeder:
            from_files.append(from_dir + os.path.normcase('/') + self.FILE_RELATIVE)
        for file in from_files:
            shutil.copy(file, to_dir + os.path.normcase('/') + \
                        FileUtils.get_relative_filename(file))
    
    def testTerminateAfterDownload(self):
        start = time.time()
        pid_tracker = Popen(self._start_tracker, shell=True)
        time.sleep(5)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_LEECHER, is_seeder=False)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_SEEDER,  is_seeder=True)
        pid_seeder = Popen(self._start_client % (self.DIRECTORY_SEEDER, ""), shell=True)
        pid_leecher = Popen(self._start_client % (self.DIRECTORY_LEECHER, "-e download -y 100"), shell=True)
        # wait for the leecher to terminate
        pid_leecher.wait()
        diff = time.time() - start
        self.assertTrue(diff < 60)
        os.system("kill -9 %i" % (pid_tracker.pid+2))
        os.system("kill -9 %i" % (pid_seeder.pid+2))
        os.system("kill -9 %i" % (pid_tracker.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+0))

    def testTerminateAfterPlayback(self):
        start = time.time()
        pid_tracker = Popen(self._start_tracker, shell=True)
        time.sleep(5)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_LEECHER, is_seeder=False)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_SEEDER,  is_seeder=True)
        pid_seeder = Popen(self._start_client % (self.DIRECTORY_SEEDER, ""), shell=True)
        pid_leecher = Popen(self._start_client % (self.DIRECTORY_LEECHER, "-e playback -y 100"), shell=True)
        # wait for the leecher to terminate
        pid_leecher.wait()
        diff = time.time() - start
        self.assertTrue(diff < 120)
        print >>sys.stderr, "############### DIFF: %i" % diff
        os.system("kill -9 %i" % (pid_tracker.pid+2))
        os.system("kill -9 %i" % (pid_seeder.pid+2))
        os.system("kill -9 %i" % (pid_tracker.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+0))
    
    def testTerminateAfterSeeding(self):
        start = time.time()
        pid_tracker = Popen(self._start_tracker, shell=True)
        time.sleep(5)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_LEECHER, is_seeder=False)
        self._copy_files_to_client(self.DIRECTORY_TRACKER, self.DIRECTORY_SEEDER,  is_seeder=True)
        pid_seeder = Popen(self._start_client % (self.DIRECTORY_SEEDER, ""), shell=True)
        pid_leecher = Popen(self._start_client % (self.DIRECTORY_LEECHER, "-e seeding 20 -y 100"), shell=True)
        # wait for the leecher to terminate
        pid_leecher.wait()
        diff = time.time() - start
        self.assertTrue(diff < 60)
        self.assertTrue(diff >= 20)
        os.system("kill -9 %i" % (pid_tracker.pid+2))
        os.system("kill -9 %i" % (pid_seeder.pid+2))
        os.system("kill -9 %i" % (pid_tracker.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+1))
        os.system("kill -9 %i" % (pid_seeder.pid+0))
        
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    #unittest.main(verbosity=2)
    
    #suite = unittest.TestSuite()
    #suite.addTest(TerminationTest())
#    suite.addTest(TerminationTest('testTerminateAfterDownload'))
    #suite.addTest(TerminationTest('testTerminateAfterPlayback'))
    #suite.addTest(TerminationTest('testTerminateAfterSeeding'))
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBiasedUnchoking)
    unittest.TextTestRunner(verbosity=2).run(suite)