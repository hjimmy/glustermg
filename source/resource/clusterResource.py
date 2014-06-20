import web
import auth
from services import clusterService

class Clusters:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def GET(self):
        return clusterService.getClusters()  
    def POST(self):
        return clusterService.createCluster()
    def PUT(self):
        return clusterService.registerCluster()

class Cluster:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def DELETE(self,clusterName):
        return clusterService.unregisterCluster(clusterName)
    def POST(self,clusterName):
        return clusterService.initCluster(clusterName)
    def PUT(self,clusterName):
        return clusterService.operationCluster(clusterName)
    def GET(self,clusterName):
        return clusterService.getCluster(clusterName)
