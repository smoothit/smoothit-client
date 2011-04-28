import os
import logging
import re
import sys

__author__ = "Markus Guenther, Konstantin Pussep"

class FileUtils:
    '''
    This class offers some static conveniance methods that are used
    by the Testbed codebase.
    '''
    def create_directory(directory, removeOld=False):
        '''
        Creates the given directory if it is not present in the file system.
        Returns true, if the directory was created ans raises an exception
        if there was a directory under the specified name that could not be
        deleted.
        '''
        if os.access(directory, os.F_OK):
            if removeOld:
                for root, dirs, files in os.walk(directory, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            else:
                raise Exception("Directory "+directory+" is not empty!")
        else:
            os.mkdir(directory)
            return True
            #return False
    create_directory = staticmethod(create_directory)
    
    def get_relative_filename(filename):
        '''
        Strips the path from a filename so that the relative filename 
        remains.
        '''
        #relname = filename.partition(os.path.normcase('/'))
        split = filename.rsplit(os.path.normcase('/'))
        if not split[-1] is "": 
            return split[-1]
        else:
            return split[-2]
    get_relative_filename = staticmethod(get_relative_filename)
    
    def get_path_from_full_filename(filename):
        '''
        Extracts and returns the full path from a given filename.
        '''
        split = filename.rsplit(os.path.normcase('/'))
        return os.path.normcase('/').join(split[:len(split)-1])
    get_path_from_full_filename = staticmethod(get_path_from_full_filename)
    
    def get_current_script_directory(file = __file__):
        '''
        Returns the directory of the script that is being executed at
        the moment. This might differ from the working directory, which
        can be obtained by calling os.getcwd()
        '''
        return os.path.dirname(os.path.realpath(file))
    get_current_script_directory = staticmethod(get_current_script_directory)
    
    def remove_directory_recursively(dir):
        '''Performs a top-to-bottom elimination of all files and directories
        which reside inside the directory dir. dir will also be deleted. Do
        not pass crucial system directories into this method, since they
        could be deleted and harm the performance of your system!'''
        # do not allow "/" to be deleted
        if dir == "/":
            return
        for root, dirs, files in os.walk(dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(dir)
    remove_directory_recursively = staticmethod(remove_directory_recursively)

def remove_duplicate_elements_from_list(seq, trafo=None):
    '''
    This function removes all duplicate elements from a list. You can also
    pass in a second argument, which allows you to transform list elements
    before they are checked, allowing you to consider for example "E" and
    "e" as identical.
    
    Originally written by Peter Bengtsson, www.peterbe.com
    '''
    if trafo is None:
        def trafo(x): return x
        
    seen = {}
    result = []
    for item in seq:
        marker = trafo(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
        
    return result

def files_list(directory, list_of_suffixes):
    '''
    Looks for files matching the suffix in the given directory and puts them in 
    a list. That list is returned to the caller.
    '''
    fileObjects = os.listdir(directory)
    
    torrents = []
    for file in fileObjects:
        for suffix in list_of_suffixes:
            if str(file).endswith(suffix):
                torrents.append(os.path.join(directory, file))
    
    return torrents

def load_test_module(module_path):
    '''
    '''
    module = __import__(module_path)
    assert module is not None
    
    tests = []
    for elem in dir(module):
        function = getattr(module, elem)
        if callable(function) and elem.startswith("test"):
            tests.append(function)
            
    return (module, tests)

def compare_odd_even(c1, c2):
    '''
    Compare two connections, the ones with even IP addresses are considered "more local" i.e. smaller.
    Connections must offer the get_ip() method, returning a string representation of IP.
    '''
    ip1_even = (int(c1.get_ip().replace(".","")) % 2 ==0) 
    ip2_even = (int(c2.get_ip().replace(".","")) % 2 == 0)
    if ip1_even == ip2_even: return 0 # equal
    elif ip1_even: return -1# only c1 is "close"
    else: return 1# only c2 is close
    
def set_exit_handler(func):
    '''Allows to set an exit handler that gets called if the running Python
    process gets killed. This can be used to clean up after the application
    has exited. The behaviour on a Windows system is a bit different.
    If you kill the Python process via the Task Manager, you will not get
    a chance to run additional cleanup code.'''
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception ("pywin32 not installed for Python " + version)
    else:
        import signal
        signal.signal(signal.SIGTERM, func)
        
def verify_tracker_url(url):
    url_pattern = re.compile('(http://)?[A-Za-z0-9.\-]+:[0-9]{4,}/announce')
    url_matcher = url_pattern.match(url)
    return (url_matcher is not None)

def extract_tracker_port_from_url(url):
    url_pattern = re.compile('(http://)?[A-Za-z0-9.\-]+:([0-9]{4,})/announce')
    url_matcher = url_pattern.match(url)
    # the port number is stored in the third group
    port = int(url_matcher.group(2))
    return port