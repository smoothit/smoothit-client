import logging
import logging.handlers
import sys
import time

from BaseLib.Core.simpledefs import *

class ReportAnalyzer:
    '''Receives status reports from clients, reduces the received information
       to a necessary minimum and tries to match the resulting data against
       user-speficied conditions during the execution of a Testbed instance.
    '''
    def __init__(self, callback=None):
        self._reports = {}
        self._joined = {}
        # injected callback function
        self._callback = callback
        
        # configure logging for this class
        # we actually need two different loggers
        # the first logger is used for debugging purposes
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(name)s: %(asctime)s - %(levelname)s - %(message)s")
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)
        consoleHandler.setFormatter(formatter)
        self._logger.addHandler(consoleHandler)
        formatter = logging.Formatter("")
        fileHandler = logging.handlers.RotatingFileHandler("analyzer.out", maxBytes=1024*1024)
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(logging.INFO)
        self._logger.addHandler(fileHandler)
        
        # empty condition lists
        self._conditions = []
        self._satisfied = []
        
    def clean(self):
        '''Reset member variables.
        '''
        self._conditions = []
        self._satisfied = []
        self._reports = {}
        self._joined = {}
        
    def _log_to_file(self, client, report):
        str = "%i\t%s\t%s\t%i" % \
        (client, report["timestamp"],
         dlstatus_strings[report["status"]],
         report["progress"])
        self._logger.info(str)
    
    def _reduce(self, report):
        new_report = {
                      "timestamp"   :   report["timestamp"],
                      "status"      :   int(report["status"]),
                      "progress"    :   report["progress"],
                      "down_total"  :   report["down_total"],
                      "down_rate"   :   report["down_rate"],
                      "up_total"    :   report["up_total"],
                      "up_rate"     :   report["up_rate"]
                      }
        
        self._logger.debug("Reduced the new report.")
        
        return new_report
    
    def _evaluate(self):
        self._logger.debug("Starting the evaluation.")
        # every evaluation function resembles a standalone testcase, so we
        # have to call every function and check its boolean return value.
        # we need to keep track of those conditions that evaluated to true
        # because we have to remove them from the conditions list AFTER we
        # iterated through it, otherwise side effects may arise
        evaluated = []
        for condition in self._conditions:
            if condition.evaluate(self._reports):
                self._logger.debug(
                    "CONDITION: %s evaluated to true." % condition.__class__.__name__)
                evaluated.append(condition)
            else:
                self._logger.debug(
                    "CONDITION: %s evaluated to false." % condition.__class__.__name__)
        
        for condition in evaluated:
            self._conditions.remove(condition)
            self._satisfied.append(condition)
        return len(self._conditions) == 0
    
    def set_conditions(self, list_of_conditions):
        '''Sets the list of conditions that shall be evaluated. Previously
           added conditions will be lost if you call this method.
        '''
        self._conditions = list_of_conditions
        
    def get_remaining_conditions(self):
        '''Returns a list of all conditions that were not satisfied
           by the time this method got called.
        '''
        return self._conditions
    
    def get_satisfied_conditions(self):
        '''Returns a list of all conditions that were satisfied
           by the time this method got called.
        '''
        return self._satisfied
    
    def satisfied_all_conditions(self):
        '''Returns a boolean value whether every given condition
           could be satisfied.
        '''
        return len(self._conditions) == 0
        
    def put_report(self, report):
        '''Clients of ReportAnalyzer use this method to dispatch a report
           to this class. Before the received report is stored for future
           reference, put_report reduces it so that only the minimum amount
           of required information remains. After that, it starts the
           evaluation against all remaining conditions (a new report
           could change the status of a remaining condition). 
        '''
        self._logger.debug("Received a new report.")
        client = report["id"]
        filename = report["filename"]

        report = self._reduce(report)
        
        # now log the important things of that report
        # to the output file
        self._log_to_file(client, report)
        
        if client not in self._reports.keys():
            # a new client joined the swarm and has send its first report
            self._reports[client] = { filename : [report]}
            self._joined[client] = report["timestamp"]
        elif filename not in self._reports[client].keys():
            # the client has started the download of a new file
            self._reports[client][filename] = [report]
        else:
            # the client submitted a subsequent report for a file that
            # he is already downloading
            self._reports[client][filename].append(report)
        
        # now, with the reports reduced to a reasonable size,
        # check if we already reached the goal state
        if self._evaluate() and self._callback is not None:
            # if we reached it, call the callback handler
            self._logger.debug("FINIS! Every condition evaluated to true!")
            self._callback()