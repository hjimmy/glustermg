import web
import auth
from services import brickService

class Brick:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def POST(self,clusterName,volumeName):
        return brickService.addBrick(clusterName,volumeName)
    def PUT(self,clusterName,volumeName):        
        return brickService.migrateBrick(clusterName,volumeName)
    def DELETE(self,clusterName,volumeName):
        return brickService.removeBrick(clusterName,volumeName)

