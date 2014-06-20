import web
import auth
from services import volumeService
        
class VolumeService:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def DELETE(self,clusterName,volumeName):
        return volumeService.removeVolume(clusterName,volumeName)
               
    def GET(self,clusterName,volumeName):
        return volumeService.getVolume(clusterName,volumeName)

    ###########        operations on volume       #############
    def PUT(self,clusterName,volumeName):
        data = web.input()
        return volumeService.manageVolume(clusterName,volumeName,data)

class VolumesService:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
        
    def GET(self,clusterName):
        try:
            detail = web.input('details')
            details = detail['details']
        except:
            details = 'false'
        return volumeService.getVolumes(clusterName, details)

    def POST(self,clusterName):
        data = web.input()
        return volumeService.createVolume(clusterName,data)

class Logs:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
        
    def GET(self, clusterName, volumeName):
        return volumeService.getLogs(clusterName, volumeName)
        
class Options:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
        
    def GET(self, clusterName, volumeName):
        return volumeService.getOptions(clusterName, volumeName)

    def POST(self, clusterName, volumeName):
        return volumeService.setOptions(clusterName, volumeName)

    def PUT(self, clusterName, volumeName):
        return volumeService.resetOptions(clusterName, volumeName)

class Download:
    def __init__(self):
        web.header('Content-Type','application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def GET(self, clusterName, volumeName):
        return volumeService.downloadLogs(clusterName, volumeName)
