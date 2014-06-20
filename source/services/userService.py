import web
import hashlib
import sys
import threading
from scripts.common import XmlHandler, Globals, Utils

db = Globals.db
lock = threading.Lock()

def getUsers():
    try:
        responseDom = XmlHandler.ResponseXml()
        usersTag = responseDom.appendTagRoute("users")
        userNameList = db.select('users',what="username")
        if len(userNameList) == 0:
            return '<users></users>'
        for user in userNameList:
            usersTag.appendChild(responseDom.createTag("user", user.username))
        return usersTag.toxml()
    except Exception, e:
        code, reval = "25101", "Error when getting users list:" + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.HTTPError(status = "400 Bad Request", data = result)

def addUser(data):
    try:
        userName = data.userName
        password = data.password
    except Exception,e:
        code, reval = "25102", "Error when adding user: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        db.select('users',where='username=$userName' ,what="*",vars=locals())
        password = hashlib.sha1("sAlT754-"+password).hexdigest()
        db.insert('users',username=userName, password=password, enabled=1)
        return None
    except Exception, e:
        code, reval = "25102", "Error when adding user" + userName + ":" + str(e)
        params = []
        params.append(userName)
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def changeUserPassword(data):
    try:
        userName = data.userName
        newPassword = data.newPassword
        oldPassword = data.oldPassword
    except Exception,e:
        code, reval = "25103", "Error when changing user's password: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        password_info = db.select('users',where='username=$userName' ,what="password",vars=locals())
        password_hash = password_info[0].password
        oldPassword_hash = hashlib.sha1("sAlT754-"+oldPassword).hexdigest()

        if password_hash == oldPassword_hash:
            newPassword_hash = hashlib.sha1("sAlT754-"+newPassword).hexdigest()
            db.update('users',where='username=$userName',password=newPassword_hash,vars=locals())
            return None
        else:
            reval = 'user and password  cannot math!'
            code, reval = "25104", "Error when changing user" + userName + "'s password : " + reval
            httpStatus = "400 Bad Request"
    except Exception, e:
        code, reval = "25103", "Error when changing user" + userName + "'s password: " + str(e)
        httpStatus = "400 Bad Request"

    params = []
    params.append(userName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = httpStatus, data = result)

def deleteUser(data):
    try:
        userName = data.userName
    except Exception,e:
        code, reval = "25106", "Error when deleting user: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        userName = data.userName
        user_info = db.select('users',where='username=$userName' ,what="*",vars=locals())
        if len(user_info) != 0:
            db.delete('users',where='username=$userName',vars=locals())
            return None
        else:
            code, reval = "25106", "Error when deleting user" + userName + ": It does not exist"
            httpStatus = "400 Bad Request"

    except Exception, e:
        code, reval = "25105", "Error when deleting user" + userName + ": " + str(e)
        httpStatus = "400 Bad Request"

    params = []
    params.append(userName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = httpStatus, data = result)

def getCifsUsers():
    try:
        lines = Utils.readFile(Globals.CIFS_USER_FILE, lines=True)
        cifsUserDom = XmlHandler.ResponseXml()
        cifsUserTag = cifsUserDom.appendTagRoute("cifsUsers")

        for line in lines:
                if not line.strip():
                    continue
                tokens = line.strip().split(":")
                cifsUserTag.appendChild(cifsUserDom.createTag("cifsUser", tokens[1]))
        return cifsUserTag.toxml()
    except Exception,e:
        code, reval = "25000", "Error when getting cifsusers: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.HTTPError(status = "400 Bad Request", data = result)

def addCifsUser(data):
    code = "25001"
    reval = ""
    try:
        userName = data.userName
        password = data.password
    except Exception,e:
        code, reval = "25001", "Error when adding cifs user: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        lock.acquire()
        uid = getUid(userName)
        if not uid:
            uid = getLastUid()
            if not uid:
                sys.stderr.write("Unable to read file %s\n" % Globals.CIFS_USER_FILE)
                reval = "Unable to read file " + Globals.CIFS_USER_FILE
                raise
            uid += 1
        else:
            reval = "This user has already existed"
            code = "25002"
            raise

        command = "%s/add_user_cifs.py %s %s %s" % (Globals.BACKEND_SCRIPT, uid, userName, password)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            reval = status["Stderr"]
            deleteCifsUser(data)
            raise
        
        if not setUid(uid, userName):
            sys.stderr.write("Failed to add the user\n")
            reval = "Failed to add the user" + userName + " to " + Globals.CIFS_USER_FILE
            deleteCifsUser(data)
            raise
        lock.release()
        return None
    except Exception,e:
        lock.release()
        reval = "Error when adding cifs user " + userName + ": " + reval
        httpStatus = "400 Bad Request"
        params = []
        params.append(userName)
        result = Utils.errorCode(code, reval, params)
        raise web.webapi.HTTPError(status = httpStatus, data = result)

def getUid(userName):
    lines = Utils.readFile(Globals.CIFS_USER_FILE, lines=True)
    for line in lines:
        tokens = line.strip().split(":")
        if tokens[1] == userName:
            return int(tokens[0])
    return None

def getLastUid():
    lines = Utils.readFile(Globals.CIFS_USER_FILE, lines=True)
    if not lines:
        return Globals.DEFAULT_UID
    return int([line.strip().split(':')[0] for line in lines if line.strip()][-1])


def setUid(uid, userName):
    try:
        fp = open(Globals.CIFS_USER_FILE, "a")
        fp.write("%s:%s\n" % (uid, userName))
        fp.close()
        return True
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_USER_FILE, str(e)))
        return False

def deleteCifsUser(data):
    code = "25003"
    reval = ""
    try:
        userName = data.userName
    except Exception,e:
        reval = "Error when deleting cifs user: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        command = "%s/delete_user_cifs.py %s " % (Globals.BACKEND_SCRIPT, userName)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            Utils.log("delete cifs user %s failure" % (userName))
            reval = status["Stderr"]
            raise
    
        if not removeUser(userName):
            Utils.log("Failed to remove cifs user %s from user.cifs" % (userName))
            reval = "Failed to remove cifs user "+ userName + " from user.cifs"
            raise
        return None
    except Exception,e:
        code,reval = "25003", "Error when delete cifs user" + userName + ": " + reval
        params = []
        params.append(userName)
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def removeUser(userName):
    lines = Utils.readFile(Globals.CIFS_USER_FILE, lines=True)
    try:
        fp = open(Globals.CIFS_USER_FILE, "w")
        for line in lines:
            if not line.strip():
                continue
## junli.li remove the line of userName from CIFS_USER_FILE
            if line.strip().split(":")[1] == userName:
                continue
            fp.write("%s" % line)
        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_USER_FILE, str(e)))
        return False
    return True

def changeCifsUserPasswd(data):
    code = "25004"
    reval = ""

    try:
        userName = data.userName
        password = data.password
    except Exception,e:
        reval = "Error when changing cifs user: " + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)

    try:
        uid = getUid(userName)
        if not uid:
            sys.stderr.write("cifsser %s not exist in %s\n" % (userName,Globals.CIFS_USER_FILE))
            reval = "cifsser " + userName + " not exist in \n" + Globals.CIFS_USER_FILE
            raise

        command = "%s/change_passwd_user_cifs.py %s %s" % (Globals.BACKEND_SCRIPT, userName, password)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            reval = status["Stderr"]
            raise
        return None
    except Exception,e:
        reval = "Error when changing cifs user" + userName + ": " + reval
        result = Utils.errorCode(code, reval, [])
        raise web.webapi.HTTPError(status = "400 Bad Request", data = result)
