##################################################
# file: IoPService_client.py
# 
# client stubs generated by "ZSI.generate.wsdl2python.WriteServiceModule"
#     /usr/bin/wsdl2py -b http://localhost:8080/sis/IoPEndpoint?wsdl
# 
##################################################

from IoPService_types import *
import urlparse, types
from ZSI.TCcompound import ComplexType, Struct
from ZSI import client
from ZSI.schema import GED, GTD
import ZSI
from ZSI.generate.pyclass import pyclass_type

# Locator
class IoPServiceLocator:
    IoPServicePort_address = "http://iridium:8080/sis/IoPEndpoint"
    def getIoPServicePortAddress(self):
        return IoPServiceLocator.IoPServicePort_address
    def getIoPServicePort(self, url=None, **kw):
        return SisIoPPortBindingSOAP(url or IoPServiceLocator.IoPServicePort_address, **kw)

# Methods
class SisIoPPortBindingSOAP:
    def __init__(self, url, **kw):
        kw.setdefault("readerclass", None)
        kw.setdefault("writerclass", None)
        # no resource properties
        self.binding = client.Binding(url=url, **kw)
        # no ws-addressing

    # op: activeInTorrents
    def activeInTorrents(self, request, **kw):
        if isinstance(request, SisIoPPort_activeInTorrents) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_activeInTorrentsResponse.typecode)
        return response

    # op: getConfigParams
    def getConfigParams(self, request, **kw):
        if isinstance(request, SisIoPPort_getConfigParams) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_getConfigParamsResponse.typecode)
        return response

    # op: getTorrentStats
    def getTorrentStats(self, request, **kw):
        if isinstance(request, SisIoPPort_getTorrentStats) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_getTorrentStatsResponse.typecode)
        return response

    # op: reportActivity
    def reportActivity(self, request, **kw):
        if isinstance(request, SisIoPPort_reportActivity) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisIoPPort_reportActivityResponse.typecode)
        return response

SisIoPPort_activeInTorrents = GED("http://iop.ws.sis.smoothit.eu/", "activeInTorrents").pyclass

SisIoPPort_activeInTorrentsResponse = GED("http://iop.ws.sis.smoothit.eu/", "activeInTorrentsResponse").pyclass

SisIoPPort_getConfigParams = GED("http://iop.ws.sis.smoothit.eu/", "getConfigParams").pyclass

SisIoPPort_getConfigParamsResponse = GED("http://iop.ws.sis.smoothit.eu/", "getConfigParamsResponse").pyclass

SisIoPPort_getTorrentStats = GED("http://iop.ws.sis.smoothit.eu/", "getTorrentStats").pyclass

SisIoPPort_getTorrentStatsResponse = GED("http://iop.ws.sis.smoothit.eu/", "getTorrentStatsResponse").pyclass

SisIoPPort_reportActivity = GED("http://iop.ws.sis.smoothit.eu/", "reportActivity").pyclass

SisIoPPort_reportActivityResponse = GED("http://iop.ws.sis.smoothit.eu/", "reportActivityResponse").pyclass