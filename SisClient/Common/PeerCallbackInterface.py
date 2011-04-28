class PeerCallbackInterface(object):
    def __init__(self):
        pass
    
    def state_callback(self, ds):
        pass
    
    def video_event_callback(self, d, event, params):
        pass