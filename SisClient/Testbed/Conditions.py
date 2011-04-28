import time

from BaseLib.Core.simpledefs import *

STATUS_TO_INT = {
                 'DLSTATUS_ALLOCATING_DISKSPACE'    :   0,
                 'DLSTATUS_WAITING4HASHCHECK'       :   1,
                 'DLSTATUS_HASHCHECKING'            :   2,
                 'DLSTATUS_DOWNLOADING'             :   3,
                 'DLSTATUS_SEEDING'                 :   4,
                 'DLSTATUS_STOPPED'                 :   5,
                 'DLSTATUS_STOPPED_ON_ERROR'        :   6}

class Condition:
    '''Defines an interface for Condition classes.
    '''
    def __init__(self):
        pass
    
    def evaluate(self, reports):
        '''Consumes a dictionary of reports and checks if the data stored
           in it alters the state of the condition from not satisfied to
           satisfied. Implementing classes should return a boolean value
           that indicates whether the condition was satisfied.
        '''
        pass
    
    def __str__(self):
        '''Implementing classes should override __str__ in order to provide
           a short status, e.g. whether the condition was satisfied and if so,
           when did that happen and so in.
        '''
        pass
    
class IsLeechingCondition(Condition):
    '''Checks if the client which is identified by a given client id acts
       as a leecher at some point in time during the execution of a Testbed
       instance, no matter in what temporal order this event occured
       and for any file the respective client is sharing.
    '''
    def __init__(self, client_id):
        self._client_id = client_id
        self._condition_start = time.time()
        self._condition_end = -1
        
    def evaluate(self, reports):
        '''See Conditions.Condition.evaluate.
        '''
        if not self._client_id in reports.keys():
            return False

        # check every download and look if the client is at least leeching
        # on one of them
        for filename in reports[self._client_id]:
            for file_reports in reports[self._client_id][filename]:
                if file_reports["status"] == DLSTATUS_DOWNLOADING:
                    self._condition_end = time.time()
                    return True
        return False
    
    def __str__(self):
        '''See Conditions.Condition.__str__.
        '''
        dispatch = "%s(clientId=%i)" % (self.__class__.__name__, self._client_id)
        if self._condition_end is not -1:
            dispatch += " satisfied after %i seconds." % (self._condition_end -
                                                          self._condition_start)
        return dispatch
    
class IsSeedingCondition(Condition):
    '''Checks if the client which is identified by a given client id acts
       as a seeder at some point in time during the execution of a Testbed
       instance, no matter in what temporal order this event occured
       and for any file the respective client is sharing.
    '''
    def __init__(self, client_id):
        self._client_id = client_id
        self._condition_start = time.time()
        self._condition_end = -1
        
    def evaluate(self, reports):
        '''See Conditions.Condition.evaluate.
        '''
        if not self._client_id in reports.keys():
            return False
        for filename in reports[self._client_id]:
            for file_reports in reports[self._client_id][filename]:
                if file_reports["status"] == DLSTATUS_SEEDING:
                    self._condition_end = time.time()
                    return True
        return False
                    
    def __str__(self):
        '''See Conditions.Condition.__str__.
        '''
        dispatch = "%s(clientId=%i)" % (self.__class__.__name__, self._client_id)
        if self._condition_end is not -1:
            dispatch += " satisfied after %i seconds." % (self._condition_end -
                                                          self._condition_start)
        return dispatch

class ReachedStatusBeforeCondition(Condition):
    '''Checks if the client identified by a given client id has reached a
       given status before a timeout expires. The implementation checks for
       the time of the first occurence of the respective status and compares
       it against the timeout.
    '''
    def __init__(self, client_id, status, filename, timeout):
        self._client_id = client_id
        self._status = status
        self._filename = filename
        self._timeout = timeout
        self._timebegin = time.time()
        
    def evaluate(self, reports):
        '''See Conditions.Condition.evaluate.
        '''
        if not self._client_id in reports.keys():
            return False
        if not self._filename in reports[self._client_id].keys():
            return False
        
        min_ts_status = -1
        for single_report in reports[self._client_id][self._filename]:
            if single_report["status"] == self._status and \
               min_ts_status == -1:
                min_ts_status = single_report["timestamp"]
                
            if single_report["status"] == self._status and \
            single_report["timestamp"] < min_ts_status:
                min_ts_status = single_report["timestamp"]
                
        # min_ts_status contains the minimum ts if there is any.
        # if there wasnt any, the ts is still -1
        if min_ts_status == -1:
            return False
        # if the found ts - the ts that represents the analyzer
        # starting time < timeout, then we can mark the condition
        # as satisfied
        return (min_ts_status - self._timebegin < self._timeout)
    
    def __str__(self):
        '''See Conditions.Condition.__str__.
        '''
        return "$s(client_id=%i,status=%i,filename=%s,timeout=%i)" % \
        (self.__class__.__name__, self._client_id, self._status, self._filename,
         self._timeout)
        
class ChangedStatusCondition(Condition):
    '''Checks if the client which is identifed by a given client id changed
       its status from status_from to status_to. This condition ensures that
       the status transition occured in temporal order.
    '''
    def __init__(self, client_id, status_from, status_to, filename):
        self._client_id = client_id
        self._status_from = STATUS_TO_INT[status_from]
        self._status_to = STATUS_TO_INT[status_to]
        self._filename = filename
        
    def evaluate(self, reports):
        '''See Conditions.Condition.evaluate.
        '''
        if not self._client_id in reports.keys():
            return False
        if not self._filename in reports[self._client_id].keys():
            return False
        
        # skim through the reports of that download and check if there was
        # was a state transition from STATE_FROM to STATE_TO
        ts_dl, ts_ul = (-1,-1)
        for single_report in reports[self._client_id][self._filename]:
            if single_report["status"] == self._status_from and \
            single_report["timestamp"] > ts_dl:
                ts_dl = single_report["timestamp"]
            
            if single_report["status"] == self._status_to and ts_ul == -1 or \
            single_report["status"] == self._status_to and \
            single_report["timestamp"] < ts_ul:
                ts_ul = single_report["timestamp"]
                
        # check if those timestamps are in temporal order
        if ts_dl != -1 and ts_ul != -1 and ts_dl <= ts_ul:
            self._transition_at = (ts_dl, ts_ul)
            return True
        
        return False
    
    def __str__(self):
        '''See Conditions.Condition.__str__.
        '''
        return "%s(client_id=%i,status_from=%s,status_to=%s,filename=%s)" % \
        (self.__class__.__name__, self._client_id, self._status_from,
         self._status_to, self._filename)
    
def FinishedDownloadCondition(client_id, filename):
    '''Creates a ChangedStatusCondition that checks if the client which is
       identified by the given client id changed its status from
       DLSTATUS_DOWNLOADING to DLSTATUS_SEEDING.
    '''
    return ChangedStatusCondition(client_id,
                               'DLSTATUS_DOWNLOADING',
                               'DLSTATUS_SEEDING',
                               filename)