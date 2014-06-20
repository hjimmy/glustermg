import re
import web
import base64
import hashlib
from scripts.common import Globals, Utils

db = Globals.db

def auth(auth_info):
    if auth_info is None:
        raise noAuthInfoError()

    auth_info = re.sub('^Basic ','',auth_info)
    userName,password = base64.decodestring(auth_info).split(':')
    password_hash = hashlib.sha1("sAlT754-"+password).hexdigest()

    try:
        ident = db.select('users',where='username=$userName and password=$password_hash',vars=locals())
        if len(ident) != 0:
            return True
        else:
            code, reval = "28003", "Authentication failed: please enter the correct user name and password. "
            httpStatus = "400 Bad Request"

    except Exception, e:
        code, reval = "28001", "Authentication failed: " + str(e)
        httpStatus = "500 Internal Server Error"

    web.header('Content-Type', 'application/xml')
    result = Utils.errorCode(code, reval, [])
    raise web.HTTPError(status = httpStatus, data = result)

def noAuthInfoError():
    code,reval = "28002", "Authentication failed: lacking of authentication information."
    result = Utils.errorCode(code, reval, [])
    httpError = web.HTTPError(status = "400 Bad Request", data = result)
    return httpError
