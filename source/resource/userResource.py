import web
import auth
from services import userService

class Users:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def GET(self):
        return userService.getUsers()
        
    def POST(self):
        data = web.input()
        userService.addUser(data)

    def PUT(self):
        data = web.input()
        userService.changeUserPassword(data)

    def DELETE(self):
        data = web.input()
        userService.deleteUser(data)

class CifsUser:
    def __init__(self):
        web.header('Content-Type', 'application/xml')
        auth_info = web.ctx.env.get('HTTP_AUTHORIZATION')
        auth.auth(auth_info)

    def GET(self):
        return userService.getCifsUsers()

    def POST(self):
        data = web.input()
        userService.addCifsUser(data)

    def DELETE(self):
        data = web.input()
        userService.deleteCifsUser(data)

    def PUT(self):
        data = web.input()
        userService.changeCifsUserPasswd(data)
