import web
import auth
from services import serverService

class Servers:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def GET(self,clusterName):
        try:
            detail = web.input('details')
            details = detail['details']
        except:
            details = 'true'
        return serverService.getServers(clusterName, details)

    def POST(self,clusterName):
        data = web.input()
        return serverService.addServerToCluster(clusterName, data)

class Server:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def GET(self,clusterName, serverName):
        return serverService.getServer(clusterName,serverName)

    def DELETE(self,clusterName,serverName):
        return serverService.removeServerFromCluster(clusterName, serverName)
    
class Disk:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def PUT(self, clusterName, serverName, diskName):
        data = web.input()
        return serverService.initDisk(clusterName, serverName, diskName, data)
        
    def get_task_info(self, clusterName, reference):
        pass

class Operation:
    def __init__(self):
        web.header('Content-Type','text/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def GET(self,clusterName,serverName):
        return serverService.getNeofsStatus(clusterName,serverName)
    def PUT(self,clusterName, serverName):
        return serverService.operationServer(clusterName,serverName)
