from BaseLib.Core import simpledefs

'''
This module holds all constants for the SIS client and cache implementations.
Constants should be used instead of plain strings to avoid typos!
'''

NS_MODE_NONE = 'none'
NS_MODE_ENABLE = 'enable'

NS_MODES_LIST = [ NS_MODE_NONE, NS_MODE_ENABLE ]

PS_MODE_NONE = 'none'
PS_MODE_ENABLE = 'enable'

PS_MODES_LIST = [ PS_MODE_NONE, PS_MODE_ENABLE ]

RS_NONE = 'none'
RS_SAME_HOST = 'samehost'
RS_GEOIP = 'geoip'
RS_ODD_EVEN = 'odd_even'
RS_SIS = 'sis'
RS_SIS_SIMPLE = 'sis_simple'
RS_IP_PRE = 'ip_pre'

RS_MODES_LIST = [ RS_NONE, RS_SAME_HOST, RS_GEOIP, RS_ODD_EVEN, RS_SIS, RS_SIS_SIMPLE, RS_IP_PRE ]

SELECTION_MODE_LOCAL = "local_folder"
SELECTION_MODE_IOP = "SIS"
SELECTION_MODE_LIST = [ SELECTION_MODE_LOCAL, SELECTION_MODE_IOP ]

#replacement policies
RP_FIFO = 'fifo'
RP_SMALLEST_SWARM = 'smallest_swarm'
RP_UNVIABLE = 'unviable'
RP_SLOWEST_SWARM = 'slowest_swarm'

RP_LIST = [ RP_FIFO, RP_SMALLEST_SWARM, RP_UNVIABLE, RP_SLOWEST_SWARM ]

EXIT_ON_ALL_FINISHED = 1
EXIT_ON_SEEDING_TIME = 2
EXIT_ON_PLAYBACK_DONE = 3

EXIT_ON_LIST = [ 'download', 'playback', 'seeding' ]

DOWNLOAD_MODES = { 'DLMODE_NORMAL'  :  simpledefs.DLMODE_NORMAL,
                   'DLMODE_VOD'     :  simpledefs.DLMODE_VOD }

CACHING_SECTION_NAME = "Caching"

PORT_RANGE_LOWER_BOUND = 10000
PORT_RANGE_UPPER_BOUND = 20000

DEFAULT_PIECE_LENGTH = 16384

TORRENT_DOWNLOAD_EXT = ".torrent"
TORRENT_VOD_EXT = ".tstream"