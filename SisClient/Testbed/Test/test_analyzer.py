import unittest
import logging

from SisClient.Testbed.Reporting.analyzer import *
from SisClient.Testbed.Conditions import *

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(TestAnalyzer("test_changed_condition"))
        suite.addTest(TestAnalyzer("test_simple_with_two_clients"))
        return suite
    
    def test_changed_condition(self):
        conditions = []
        conditions.append(ChangedStatusCondition(
            1, 'DLSTATUS_HASHCHECKING',
            'DLSTATUS_DOWNLOADING', 'test.rar'))
        conditions.append(ChangedStatusCondition(
            1, 'DLSTATUS_DOWNLOADING',
            'DLSTATUS_SEEDING', 'test.rar'))
        
        analyzer = ReportAnalyzer()
        analyzer.set_conditions(conditions)
        
        report1 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_HASHCHECKING,
              "progress": 0.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
    
        report2 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_DOWNLOADING,
              "progress": 0.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
    
        report3 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_SEEDING,
              "progress": 100.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
        
        analyzer.put_report(report1)
        analyzer.put_report(report2)
        analyzer.put_report(report3)
        
        self.assertTrue(analyzer.satisfied_all_conditions())
        self.assertEquals(0, len(analyzer.get_remaining_conditions()))
        self.assertEquals(2, len(analyzer.get_satisfied_conditions()))

    def test_reached_status_before_no_status(self):
        conditions = []
        conditions.append(ReachedStatusBeforeCondition(1,
                                                       DLSTATUS_SEEDING,
                                                       "test.rar",
                                                       2))
        analyzer = ReportAnalyzer()
        analyzer.set_conditions(conditions)
        
        report1 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }

        analyzer.put_report(report1)
        
        self.assertFalse(analyzer.satisfied_all_conditions())
        self.assertEquals(1, len(analyzer.get_remaining_conditions()))
        self.assertEquals(0, len(analyzer.get_satisfied_conditions()))

    def test_reached_status_before_too_late(self):
        conditions = []
        conditions.append(ReachedStatusBeforeCondition(1,
                                                       DLSTATUS_SEEDING,
                                                       "test.rar",
                                                       2))
        analyzer = ReportAnalyzer()
        analyzer.set_conditions(conditions)
        
        report1 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report1)
                
        report2 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report2)
        
        report3 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report3)
        
        report4 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report4)
        
        report5 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_SEEDING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }

        time.sleep(1)
        analyzer.put_report(report5)

        self.assertFalse(analyzer.satisfied_all_conditions())
        self.assertEquals(1, len(analyzer.get_remaining_conditions()))
        self.assertEquals(0, len(analyzer.get_satisfied_conditions()))
        
    def test_reached_status_before(self):
        conditions = []
        conditions.append(ReachedStatusBeforeCondition(1,
                                                       DLSTATUS_SEEDING,
                                                       "test.rar",
                                                       8))
        analyzer = ReportAnalyzer()
        analyzer.set_conditions(conditions)
        
        report1 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report1)
                
        report2 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report2)
        
        report3 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report3)
        
        report4 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_DOWNLOADING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }
        
        time.sleep(1)
        analyzer.put_report(report4)
        
        report5 = {
            "id" : 1,
            "filename" : "test.rar",
            "timestamp" : time.time(),
            "status" : DLSTATUS_SEEDING,
            "progress" : 0.0,
            "down_total" : 0.0,
            "down_rate" : 0.0,
            "up_total" : 0.0,
            "up_rate" : 0.0
            }

        time.sleep(1)
        analyzer.put_report(report5)

        self.assertTrue(analyzer.satisfied_all_conditions())
        self.assertEquals(0, len(analyzer.get_remaining_conditions()))
        self.assertEquals(1, len(analyzer.get_satisfied_conditions()))
    
    def test_simple_with_two_clients(self):
        conditions = []
        conditions.append(IsLeechingCondition(1))
        conditions.append(IsSeedingCondition(1))
        conditions.append(IsSeedingCondition(2))
        conditions.append(FinishedDownloadCondition(1, "test.rar"))
        
        analyzer = ReportAnalyzer()
        analyzer.set_conditions(conditions)
        
        report1 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_HASHCHECKING,
              "progress": 0.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
    
        report2 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_DOWNLOADING,
              "progress": 0.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
    
        report3 = {
              "id" : 2,
              "filename" : "test.rar",
              "timestamp": time.time(),
              "status" : DLSTATUS_SEEDING,
              "progress": 100.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }
    
        report4 = {
              "id" : 1,
              "filename" : "test.rar",
              "timestamp": time.time()+1000,
              "status" : DLSTATUS_SEEDING,
              "progress": 100.0,
              "down_total" : 0.0,
              "down_rate" : 0.0,
              "up_total": 0.0,
              "up_rate":0.0
              }

        analyzer.put_report(report1)
        analyzer.put_report(report2)
        analyzer.put_report(report3)
        analyzer.put_report(report4)

        self.assertTrue(analyzer.satisfied_all_conditions())
        self.assertEquals(0, len(analyzer.get_remaining_conditions()))
        self.assertEquals(4, len(analyzer.get_satisfied_conditions()))
        
def main():
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
    
if __name__ == "__main__":
    main()