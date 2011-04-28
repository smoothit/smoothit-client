import unittest
import logging

from test_analyzer import *
from test_testbedclientconf import *
from test_testbedconf import *
from test_testbedconfchecker import *
from test_testbedtracker import *
from test_tracker import *

if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    suite = unittest.TestSuite((
                    unittest.makeSuite(TestbedConfigCheckerTest, 'test'),
                    unittest.makeSuite(TestbedTrackerTest, 'test'),
                    unittest.makeSuite(TestbedConfigTest, 'test'),
                    unittest.makeSuite(TestbedClientConfTest, 'test'),
                    unittest.makeSuite(TestAnalyzer, 'test'),
                    unittest.makeSuite(TrackerTest, 'test')
    ))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(len(result.errors) + len(result.failures))