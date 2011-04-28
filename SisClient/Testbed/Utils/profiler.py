import os
import time

'''Code adapted from Jean Brouwers.
   See also: http://code.activestate.com/recipes/286222/
'''

_proc_status_template = '/proc/%d/status'
_scale = {'kB'  :   1024.0,
          'KB'  :   1024.0,
          'mB'  :   1024.0*1024.0,
          'MB'  :   1024.0*1024.0}

def memory(pid, since=0.0):
    '''Return memory usage in bytes.
    '''
    return (time.time(), proc_status_value(pid, 'VmSize:') - since)

def resident(pid, since=0.0):
    '''Return resident memory usage in bytes.
    '''
    return (time.time(), proc_status_value(pid, 'VmRSS:') - since)

def stacksize(pid, since=0.0):
    '''Return stack size in bytes.
    '''
    return (time.time(), proc_status_value(pid, 'VmStk:') - since)

def proc_status_value(pid, key):
    global _proc_status_template
    global _scale
    
    proc_status = _proc_status_template % pid

    try:
        t = open(proc_status)
        v = t.read()
        t.close()
    except:
        return 0.0

    i = v.index(key)
    v = v[i:].split(None, 3)
    
    if len(v) < 3:
        return 0.0
    
    return float(v[1]) * _scale[v[2]]