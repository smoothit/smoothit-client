#!/usr/bin/python

from __future__ import with_statement
import os
import re
#import GeoIP
import pygeoip
import sys

gi_city = pygeoip.GeoIP("resources/GeoLiteCity.dat")
gi_isp = pygeoip.GeoIP("resources/GeoIPISP.dat")
#gi_city = GeoIP.open("resources/GeoLiteCity.dat",GeoIP.GEOIP_STANDARD)
#gi_isp = GeoIP.open("resources/GeoIPISP.dat",GeoIP.GEOIP_STANDARD)

def maxmind_test():
    print sys.argv
    if (len(sys.argv)>1):
        ips = sys.argv[1:]
    else:
        ips = ["84.167.86.109"]

    gir = gi_city.record_by_name("www.kaune.ws")
    print "try www.kaune.ws", gir, "\n"
    
    for ip in ips:
        
        print "LOOKUP "+ip
        
        print "try isps"
        gir = gi_isp.org_by_addr(ip)
        print "ISP is ", gir
        
        print "try cities"
        #print " Available functions \n", dir(gi_city), "\n\n"
        gir = gi_city.record_by_addr(ip)
        #gir = gi_city.record_by_addr(ip)
        print gir
        
        if gir != None:
            print "Country_code", gir['country_code']
            print gir['country_code3']
            print gir['country_name']
            print gir['city']
            #print gir['region']
            print gir['region_name']
            print gir['postal_code']
            print gir['latitude']
            print gir['longitude']
            #print gir['area_code']
            #print gir['time_zone']
            if gir.has_key("metro_code"):
                print "Metro code", gir['metro_code']
            
        info_isp = gi_isp.org_by_name(ip)
        print "ISP is ", info_isp
        
        #print "city=", get_city(ip)
        #print "country=", get_country(ip)
        #print "region=", get_region_name(ip)

def get_city(ip):
    gir =  gi_city.record_by_addr(ip)
    return gir['city']

def get_country(ip):
    gir =  gi_city.record_by_addr(ip)
    return gir['country_name']

def get_region_name(ip):
    gir =  gi_city.record_by_addr(ip)
    return gir['region_name']

def get_country_code(ip):
    gir =  gi_city.record_by_addr(ip)
    return gir['country_code']

def get_isp(ip):
    return gi_isp.org_by_name(ip)

if __name__ == '__main__':
    maxmind_test()
