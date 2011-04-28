#!/usr/bin/env python
# encoding: utf-8
"""
playground.py

Created by Konstantin Pussep on 2009-07-10.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

"""

import logging
import socket
#import GeoIP
import pygeoip

def main():
    levels = {"DEBUG":logging.DEBUG, "INFO":logging.INFO, "WARN":logging.WARN, "ERROR":logging.ERROR, "CRITICAL":logging.CRITICAL, "FATAL":logging.FATAL}
    print levels
    print levels["DEBUG"]
    
    a = [0,1,2,3,4,5]
    print a
    b = [2,4,6]
    
    a.extend(b[2:3])
    print a
    del b[1:3]
    print b

    b = a[3:5]
    print b
    del b[0]
    print b
    print a
    
    x = 4.67
    y= int(x)
    print y
    print a[y]
    
    g = [3,8,1,5]
    print sorted(g)
    print g
    
    print float('0.976')
        
    # try ip conversions
    binary = socket.inet_aton("130.83.139.168")
    print binary
    dotted = socket.inet_ntoa(binary)
    print dotted
    
    #try_tribler_geo_ip()
    
    #try_geo_ip("./resources/GeoIPISP.dat")
    
    try_geo_ip("./resources/GeoLiteCity.dat")
    
def try_geo_ip(geo_ip_lib):
    print "try GeoIP ISP from lib "+geo_ip_lib
    gic = pygeoip.GeoIP(geo_ip_lib)
    #gi_isp = GeoIP.open(geo_ip_lib,GeoIP.GEOIP_STANDARD)
    info = gic.record_by_addr('64.233.161.99')
    #info_isp = gi_isp.org_by_name("193.99.144.85")
    print info
    
    print gic.record_by_addr("130.83.139.168")

if __name__ == '__main__':
    main()
