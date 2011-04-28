##################################################
# file: ClientService_server.py
#
# skeleton generated by "ZSI.generate.wsdl2dispatch.ServiceModuleWriter"
#      /usr/bin/wsdl2py -o SisClient/PeerSelection/WebService http://127.0.0.1:8080/sis/ClientEndpoint?wsdl
#
##################################################

from ZSI.schema import GED, GTD
from ZSI.TCcompound import ComplexType, Struct
from ClientService_types import *
from ZSI.ServiceContainer import ServiceSOAPBinding

# Messages  
SisClientPort_add = GED("http://client.ws.sis.smoothit.eu/", "add").pyclass

SisClientPort_addResponse = GED("http://client.ws.sis.smoothit.eu/", "addResponse").pyclass

SisClientPort_getRankedPeerList = GED("http://client.ws.sis.smoothit.eu/", "getRankedPeerList").pyclass

SisClientPort_getRankedPeerListResponse = GED("http://client.ws.sis.smoothit.eu/", "getRankedPeerListResponse").pyclass

SisClientPort_getSimpleRankedPeerList = GED("http://client.ws.sis.smoothit.eu/", "getSimpleRankedPeerList").pyclass

SisClientPort_getSimpleRankedPeerListResponse = GED("http://client.ws.sis.smoothit.eu/", "getSimpleRankedPeerListResponse").pyclass


# Service Skeletons
class ClientService(ServiceSOAPBinding):
    soapAction = {}
    root = {}

    def __init__(self, post='/sis/ClientEndpoint', **kw):
        ServiceSOAPBinding.__init__(self, post)

    def soap_add(self, ps, **kw):
        request = ps.Parse(SisClientPort_add.typecode)
        return request,SisClientPort_addResponse()

    soapAction[''] = 'soap_add'
    root[(SisClientPort_add.typecode.nspname,SisClientPort_add.typecode.pname)] = 'soap_add'

    def soap_getRankedPeerList(self, ps, **kw):
        request = ps.Parse(SisClientPort_getRankedPeerList.typecode)
        return request,SisClientPort_getRankedPeerListResponse()

    soapAction[''] = 'soap_getRankedPeerList'
    root[(SisClientPort_getRankedPeerList.typecode.nspname,SisClientPort_getRankedPeerList.typecode.pname)] = 'soap_getRankedPeerList'

    def soap_getSimpleRankedPeerList(self, ps, **kw):
        request = ps.Parse(SisClientPort_getSimpleRankedPeerList.typecode)
        return request,SisClientPort_getSimpleRankedPeerListResponse()

    soapAction[''] = 'soap_getSimpleRankedPeerList'
    root[(SisClientPort_getSimpleRankedPeerList.typecode.nspname,SisClientPort_getSimpleRankedPeerList.typecode.pname)] = 'soap_getSimpleRankedPeerList'
