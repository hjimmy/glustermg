import web
import auth
from services import taskService

class Tasks:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def GET(self,clusterName):
        return taskService.getTasks(clusterName)
class Task:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)
    def GET(self,clusterName,taskID):
        return taskService.getTask(clusterName,taskID)
    def PUT(self,clusterName,taskID):
        return taskService.managerTask(clusterName,taskID)
    def DELETE(self,clusterName,taskID):
        return taskService.deleteTask(clusterName,taskID)
