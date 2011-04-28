==============================================================================
                             Next-Share: 
      The next generation Peer-to-Peer content delivery platform
    
                       http://www.p2p-next.org/
==============================================================================

LICENSE
-------
See LICENSE.txt.


PREREQUISITES
-------------

To run the Next-Share platform from source you will need to install the
following software packages. See www.p2p-next.org for binary distributions.

    Python >= 2.4 
    OpenSSL >= 0.9.8 (with Elliptic Curve crypto support enabled, use 
                      "enable-ec" to build)
    swig >= 1.3.25
    M2Crypto >= 0.16
    apsw >= 3.6.x
    pywin32 >= Build 208 (Windows only, for e.g. UPnP support)

    wxPython >= 2.8 UNICODE (i.e., use --enable-unicode to build)
    vlc >= 0.8.6a and its python bindings (for internal video player)


Next-Share runs on Windows (XP,Vista), Mac OS X and Linux. On Linux, it is 
easiest to try to install these packages via a package manager such as
Synaptic (on Ubuntu). To run from the source on Windows it is easiest to use
binary distribution of all packages. As of Python 2.4.4 the problem with
interfacing with OpenSSL has disappeared. On Mac, we advice to use MacPorts.

INSTALLING ON LINUX
-------------------
 
1. Unpack the main source code.

2. Change to the Next-Share directory.

2. The peer-to-peer video player SwarmPlayer that is part of Next-Share can now
   be started by running

     PYTHONPATH="$PYTHONPATH":Next-Share:.
     export PYTHONPATH
     python2.4 BaseLib/Player/swarmplayer.py
  

INSTALLING ON WINDOWS
---------------------

1. Unpack the main source code.

2. Open an CMD Prompt, change to the Next-Share directory.
   
3. The peer-to-peer video player SwarmPlayer that is part of Next-Share can now
   be started by running

     set PYTHONPATH=%PYTHONPATH%:Next-Share:.
     C:\Python24\python2.4.exe BaseLib\Player\swarmplayer.py
   

Arno Bakker, 2008-11-12
