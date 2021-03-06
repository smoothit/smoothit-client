################################################## 
# IoPService_services.py 
# generated by ZSI.generate.wsdl2python
##################################################


from IoPService_services_types import *
import urlparse, types
from ZSI.TCcompound import ComplexType, Struct
from ZSI import client
import ZSI

# Locator
class IoPServiceLocator:
    SisIoPPort_address = "http://127.0.0.1:8080/sis/IoPEndpoint"
    def getSisIoPPortAddress(self):
        return IoPServiceLocator.SisIoPPort_address
    def getSisIoPPort(self, url=None, **kw):
        return SisIoPPortBindingSOAP(url or IoPServiceLocator.SisIoPPort_address, **kw)

# Methods
class SisIoPPortBindingSOAP:
    def __init__(self, url, **kw):
        kw.setdefault("readerclass", None)
        kw.setdefault("writerclass", None)
        # no resource properties
        self.binding = client.Binding(url=url, **kw)
        # no ws-addressing

    # op: activeInTorrents
    def activeInTorrents(self, request):
        if isinstance(request, SisIoPPort_activeInTorrents) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        kw = {}
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_activeInTorrentsResponse.typecode)
        return response

    # op: getPeerList
    def getPeerList(self, request):
        if isinstance(request, SisIoPPort_getPeerList) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        kw = {}
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_getPeerListResponse.typecode)
        return response

    # op: getStats
    def getStats(self, request):
        if isinstance(request, SisIoPPort_getStats) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        kw = {}
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_getStatsResponse.typecode)
        return response

    # op: getTorrentStats
    def getTorrentStats(self, request):
        if isinstance(request, SisIoPPort_getTorrentStats) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        kw = {}
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_getTorrentStatsResponse.typecode)
        return response

SisIoPPort_activeInTorrents = ns0.activeInTorrents_Dec().pyclass

SisIoPPort_activeInTorrentsResponse = ns0.activeInTorrentsResponse_Dec().pyclass

SisIoPPort_getPeerList = ns0.getPeerList_Dec().pyclass

SisIoPPort_getPeerListResponse = ns0.getPeerListResponse_Dec().pyclass

SisIoPPort_getStats = ns0.getStats_Dec().pyclass

SisIoPPort_getStatsResponse = ns0.getStatsResponse_Dec().pyclass

SisIoPPort_getTorrentStats = ns0.getTorrentStats_Dec().pyclass

SisIoPPort_getTorrentStatsResponse = ns0.getTorrentStatsResponse_Dec().pyclass
