#!/bin/bash
# created by Konstantin Pussep

# default SIS url
URL=http://127.0.0.1:8080/sis/ClientEndpoint?wsdl

# select your torrent here
#TORRENT=torrents/2012.torrent
#TORRENT=torrents/mirrors-edge.torrent
#TORRENT="torrents/[isoHunt]Australia_2008_DVDSCR_XviD-KingBen_(Kingdom-Release).4671112.TPB.torrent"
TORRENT="torrents/Big_Buck_Bunny_1080p_surround_frostclick.com_frostwire.com.torrent"
#TORRENT="torrents/startrek.torrent"

#CMD="BaseLib/Tools/bitbucket-live-noauth.py $TORRENT"
CMD="python SisClient/Tools/swarmplayer-sis.py"
#CMD=SisClient/Tools/headless.py
#CLIENT_STUB="SisClient/PeerSelection/WebService/ClientService_services.py"
CLIENT_STUB="SisClient/PeerSelection/WebService/ClientService_client.py"

# set python path
export PYTHONPATH="$PYTHONPATH":lib:.

echo "Params are $*"
$CMD $*
