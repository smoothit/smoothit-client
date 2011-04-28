'''
SupporterMonitor.py:
====================
This module realizes a tracker-side extension which enables the Tribler system
to include supporter servers in order to supply starving VoD peers with the chunks they need to 
sustain their playback.
 
Essential parts of the module include:
* Classes that help to maintain internal state information as seen by the supporter monitor 
  (see MonitoredPeer, MonitoredSupporter)
* Classes that help to represent the state a monitored peer currently resides in (see State and all
 its subclasses).
* Utility classes that help to establish a communication between peers or can be used to summarize 
  the complete state of the monitor.
* The monitor class itself, which manages supporters and supportees and organizes the internal 
  dispatching of incoming requests as well as sending the necessary information to participating 
  components (e.g. supporter peers).

State transitions are modeled after (Gerlach, 2010). The transition system is shown underneath.

   +-----------+  buffer not full msg  +-----------+
   |           |---------------------->|           |
   |  DEFAULT  |                       |  WATCHED  |
   |           |<----------------------|           |
   +-----------+  buffer full msg      +-----------+
        ^                                    |
        |                                    |
        | peer sends                         | k buffer not full
        | buffer full msg                    | msgs over last
        | and timer runs                     | k*(1+0.150) sek.
        | out                                |
        |                                    |
        |                                    v
  +-------------+                      +------------+
  |             |                      |            |
  |  SUPPORTED  |<---------------------|  STARVING  |
  |             |  >= minPeers starv.  |            |
  +-------------+  or supporter has    +------------+
                   < maxPeers 

For further details, please consult the PyDoc-commentary at class-level.

Supporter.py
============
Implements a very simple peer that offers an XML-RPC interface over which it is able receive
lists of peers that the peer shall support with required chunks. The supporter changes the
behaviour of the classic choke-algorithm as defined in BaseLib.Core.BitTornado.BT1.Choker,
since it only unchokes those peers that the receives from a SupporterMonitor via the
beforementioned interface.

For further details, please consult the PyDoc-commentary at class-level.
'''