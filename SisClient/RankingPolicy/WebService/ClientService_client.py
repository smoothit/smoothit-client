##################################################
# file: ClientService_client.py
# 
# client stubs generated by "ZSI.generate.wsdl2python.WriteServiceModule"
#     /usr/bin/wsdl2py -o SisClient/PeerSelection/WebService http://127.0.0.1:8080/sis/ClientEndpoint?wsdl
# 
##################################################

from ClientService_types import *
#import ClientService_types
import urlparse, types
from ZSI.TCcompound import ComplexType, Struct
from ZSI import client
from ZSI.schema import GED, GTD
import ZSI

# Locator
class ClientServiceLocator:
    ClientServicePort_address = "http://127.0.0.1:8080/sis/ClientEndpoint"
    def getClientServicePortAddress(self):
        return ClientServiceLocator.ClientServicePort_address
    def getClientServicePort(self, url=None, **kw):
        return SisClientPortBindingSOAP(url or ClientServiceLocator.ClientServicePort_address, **kw)

# Methods
class SisClientPortBindingSOAP:
    def __init__(self, url, **kw):
        kw.setdefault("readerclass", None)
        kw.setdefault("writerclass", None)
        # no resource properties
        self.binding = client.Binding(url=url, **kw)
        # no ws-addressing
        self.url = url

    # op: add
    def add(self, request, **kw):
        if isinstance(request, SisClientPort_add) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisClientPort_addResponse.typecode)
        return response

    # op: getRankedPeerList
    def getRankedPeerList(self, request, **kw):
        if isinstance(request, SisClientPort_getRankedPeerList) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisClientPort_getRankedPeerListResponse.typecode)
        return response

    # op: getSimpleRankedPeerList
    def getSimpleRankedPeerList(self, request, **kw):
        if isinstance(request, SisClientPort_getSimpleRankedPeerList) is False:
            raise TypeError, "%s incorrect request type" % (request.__class__)
        # no input wsaction
        self.binding.Send(None, None, request, soapaction="", **kw)
        # no output wsaction
        response = self.binding.Receive(SisClientPort_getSimpleRankedPeerListResponse.typecode)
        return response

SisClientPort_add = GED("http://client.ws.sis.smoothit.eu/", "add").pyclass

SisClientPort_addResponse = GED("http://client.ws.sis.smoothit.eu/", "addResponse").pyclass

SisClientPort_getRankedPeerList = GED("http://client.ws.sis.smoothit.eu/", "getRankedPeerList").pyclass

SisClientPort_getRankedPeerListResponse = GED("http://client.ws.sis.smoothit.eu/", "getRankedPeerListResponse").pyclass

SisClientPort_getSimpleRankedPeerList = GED("http://client.ws.sis.smoothit.eu/", "getSimpleRankedPeerList").pyclass

SisClientPort_getSimpleRankedPeerListResponse = GED("http://client.ws.sis.smoothit.eu/", "getSimpleRankedPeerListResponse").pyclass
