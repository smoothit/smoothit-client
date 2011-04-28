from threading import Thread, Timer
from SisClient.Utils.common_utils import get_id
import sys
import traceback
from BaseLib.Core.API import TorrentDef

def start_cache_console(cache_instance):
    ''' Starts the CacheConsole.
    '''
    
    console = CacheConsole(cache_instance)
    console.start()


class CacheConsole(Thread):
    ''' The CacheConsole allows to manually  control the cache.
    '''
    
    run = True
    
    def __init__(self, cache = None):
        self.status = None
        Thread.__init__(self)
        sys.stdout = sys.stderr
        self.cache = cache
        
        self.actions = {'help' : self.print_help, 'status': self.print_status,
                        'config' : self.print_config, 'torrents': self.print_torrents,
                        'delete' : self.delete, 'add' : self.add, 
                        'test' : self.test, 'exit' : self.exit}
        
    def print_prompt(self):
        self.print_status([])
        print str(self.actions.keys())+' >>'
        
    def run(self):
        #print >> sys.stderr, 'console started'
        self.status_timer = Timer(2.0, self.print_prompt)
        self.status_timer.start() # regularly print status messages
        while self.run:
            sys.stdout = sys.stderr            
            prompt = str(self.actions.keys())+' >>'
            input = raw_input(prompt)
            self.process_input(input)

    def print_config(self, params):
        print >> sys.stderr, 'Current configuration:'
        for (key, value) in self.cache.own_config.static_data.items():
            print >> sys.stderr, "%s: %s" % (key, value) 
    
    def print_help(self, params):
        ''' print help. '''
        #print >> sys.stderr,'commands: \nstatus-  \nadd \'filepath\' -  \ndelete \'       
        print >> sys.stderr,"########## Available commands are: ############"     
        for name, method in self.actions.items():
            print >> sys.stderr, "<%s> :\t%s" % ( name, str(method.__doc__))
        return
    
    def print_torrents(self, params):
        for td in self.cache.torrent_selection.get_torrents():
            print >> sys.stderr, "torrent files: ", td.get_files() 
    
    def print_status(self, params):
        ''' shows the current status of the cache. '''
        self.status = self.cache.get_status()
        self.status.print_to_console()
    
    def delete(self, params):
        ''' 'id\' - deletes the specified download. '''
        if len(params) == 2:
            index = int(params[1])
            id = self.status.downloadstats[index-1]['id']
            self.cache.leave_swarm(id)
            return
        
    def add(self, params):
        ''' adds a new download. '''
        if len(params) == 0:
            print >> sys.stderr, "Please provide torrent path."
        else:  
            path = params[1]
            tdef = TorrentDef.load(path)
            t_id = get_id(tdef)
            if not self.cache.is_running(t_id):
                self.cache.join_swarm(tdef, t_id)
        
    def test(self, params):
        ''' help for test! '''
        
        print  >> sys.stderr, "Test succeed, help string: ",  self.test.__doc__
        print  >> sys.stderr, "params are: ", params
        
    def exit(self, params):
        ''' Stop cache and exit the console.'''
        #TODO: call session.shutdown???
        sys.exit(0)
                
    def process_input(self, input):
        split = input.split(' ')
        
        if len(split) > 0:
            chosen = split[0]
            #print >> sys.stderr, "input string:"
            call = self.actions.get(chosen, self.print_help)
            #print >> sys.stderr, "chosen action: ", call
            try:
                call(split[1:])
            except SystemExit:
                raise # don't catch exit command
            except:
                traceback.print_exc()
                #print sys.exc_info()
        else: # will never happen ;) split is at least a list with one space!
            print >> sys.stderr,"please choose action"
               
        #print >> sys.stderr, 'invalid input'
        
    
#start_cache_console(None)
    