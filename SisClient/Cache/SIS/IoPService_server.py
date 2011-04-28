##################################################
# file: IoPService_server.py
#
# skeleton generated by "ZSI.generate.wsdl2dispatch.ServiceModuleWriter"
#      /usr/bin/wsdl2py -b http://localhost:8080/sis/IoPEndpoint?wsdl
#
##################################################

from ZSI.schema import GED, GTD
from ZSI.TCcompound import ComplexType, Struct
from IoPService_types import *
from ZSI.ServiceContainer import ServiceSOAPBinding

# Messages  
SisIoPPort_activeInTorrents = GED("http://iop.ws.sis.smoothit.eu/", "activeInTorrents").pyclass

SisIoPPort_activeInTorrentsResponse = GED("http://iop.ws.sis.smoothit.eu/", "activeInTorrentsResponse").pyclass

SisIoPPort_getConfigParams = GED("http://iop.ws.sis.smoothit.eu/", "getConfigParams").pyclass

SisIoPPort_getConfigParamsResponse = GED("http://iop.ws.sis.smoothit.eu/", "getConfigParamsResponse").pyclass

SisIoPPort_getTorrentStats = GED("http://iop.ws.sis.smoothit.eu/", "getTorrentStats").pyclass

SisIoPPort_getTorrentStatsResponse = GED("http://iop.ws.sis.smoothit.eu/", "getTorrentStatsResponse").pyclass

SisIoPPort_reportActivity = GED("http://iop.ws.sis.smoothit.eu/", "reportActivity").pyclass

SisIoPPort_reportActivityResponse = GED("http://iop.ws.sis.smoothit.eu/", "reportActivityResponse").pyclass


# Service Skeletons
class IoPService(ServiceSOAPBinding):
    soapAction = {}
    root = {}

    def __init__(self, post='/sis/IoPEndpoint', **kw):
        ServiceSOAPBinding.__init__(self, post)

    def soap_activeInTorrents(self, ps, **kw):
        request = ps.Parse(SisIoPPort_activeInTorrents.typecode)
        return request,SisIoPPort_activeInTorrentsResponse()

    soapAction[''] = 'soap_activeInTorrents'
    root[(SisIoPPort_activeInTorrents.typecode.nspname,SisIoPPort_activeInTorrents.typecode.pname)] = 'soap_activeInTorrents'

    def soap_getConfigParams(self, ps, **kw):
        request = ps.Parse(SisIoPPort_getConfigParams.typecode)
        return request,SisIoPPort_getConfigParamsResponse()

    soapAction[''] = 'soap_getConfigParams'
    root[(SisIoPPort_getConfigParams.typecode.nspname,SisIoPPort_getConfigParams.typecode.pname)] = 'soap_getConfigParams'

    def soap_getTorrentStats(self, ps, **kw):
        request = ps.Parse(SisIoPPort_getTorrentStats.typecode)
        return request,SisIoPPort_getTorrentStatsResponse()

    soapAction[''] = 'soap_getTorrentStats'
    root[(SisIoPPort_getTorrentStats.typecode.nspname,SisIoPPort_getTorrentStats.typecode.pname)] = 'soap_getTorrentStats'

    def soap_reportActivity(self, ps, **kw):
        request = ps.Parse(SisIoPPort_reportActivity.typecode)
        return request,SisIoPPort_reportActivityResponse()

    soapAction[''] = 'soap_reportActivity'
    root[(SisIoPPort_reportActivity.typecode.nspname,SisIoPPort_reportActivity.typecode.pname)] = 'soap_reportActivity'
