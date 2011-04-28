import logging

from SisClient.Common.PeerCallbackInterface import PeerCallbackInterface

class PeerCallbackHandlers(PeerCallbackInterface):
    def __init__(self, name, report_interval):
        self.reporters = []
        self._logger = logging.getLogger("Status.%s" % self.__class__.__name__)
        self.interval = int(report_interval)
        
    def register_handler(self, reporter):
        if reporter == None:
            raise Exception('Illegal argument to register_handler')
        self.reporters.append(reporter)
        
    def unregister_handler(self, reporter):
        if reporter == None:
            raise Exception('Illegal argument to unregister_handler')
        if reporter not in self.reporters:
            raise Exception('Illegal state: The reporter was not registered before.')
        self.reporters.remove(reporter)
        
    def state_callback(self, ds):
        #self._logger.error("Dispatch state callback to %i reporters" % len(self.reporters))
        for reporter in self.reporters:
            reporter.state_callback(ds)
        return (self.interval, True)
    
    def video_event_callback(self, d, event, params):
        for reporter in self.reporters:
            reporter.video_event_callback(d, event, params)