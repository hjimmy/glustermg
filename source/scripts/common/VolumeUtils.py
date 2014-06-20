import os
import sys
import web
import re

from XmlHandler import *
from XmlHandler import XDOM,ResponseXml
import xml.etree.ElementTree as ET

p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/scripts/common" % os.path.dirname(p1)
p3 = "%s/scripts/gateway" % os.path.dirname(p1)
p4 = "%s/scripts/backend" % os.path.dirname(p1)

if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
if not p3 in sys.path:
    sys.path.append(p3)
if not p4 in sys.path:
    sys.path.append(p4)
from Globals import *
import Utils

def readVolumeSmbConfFile(fileName=Globals.VOLUME_SMBCONF_FILE):
    entryList = []
    lines = Utils.readFile(fileName, lines=True)
    for line in lines:
        tokens = line.split("#")[0].strip().split(";")[0].strip().split("=")
        if len(tokens) != 2:
            continue
        if tokens[0].strip().upper() == "INCLUDE":
            entryList.append(tokens[1].strip())
    return entryList

def writeVolumeSmbConfFile(entryList, fileName=Globals.VOLUME_SMBCONF_FILE):
    try:
        fp = open(fileName, "w")
        for entry in entryList:
            fp.write("include = %s\n" % entry)
        fp.close()
        return True
    except IOError, e:
        Utils.log("Failed to write file %s: %s" % (fileName, str(e)))
        return False

def includeVolume(volumeName, fileName=Globals.VOLUME_SMBCONF_FILE):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    if not os.path.exists(volumeFile):
        return False
    entryList = readVolumeSmbConfFile(fileName)
    if volumeFile in entryList:
        return True
    entryList.append(volumeFile)
    return writeVolumeSmbConfFile(entryList, fileName)

def excludeVolume(volumeName, fileName=Globals.VOLUME_SMBCONF_FILE):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    entryList = readVolumeSmbConfFile(fileName)
    if not os.path.exists(volumeFile):
        return True
    if volumeFile not in entryList:
        return True
    entryList.remove(volumeFile)
    Utils.log("entryList = %s" % entryList)
    return writeVolumeSmbConfFile(entryList, fileName)

#   ######added by liub        ######
def modifyUsersConfig(volumeName):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    valid_users=[]
    if not os.path.exists(volumeFile):
        return True
    try:
        lines = Utils.readFile(volumeFile, lines=True)
        for line in lines:
            if "valid users" in line:
                valid_users=[line.split('#')[0].strip().split('=')[1].strip()]
        for user in valid_users:
            try:
                user_config="/etc/glustermg/volumes/users/%s-%s.smbconf"%(volumeName,str(user))
                if not os.path.exists(user_config):
                    return True
                os.remove(user_config)
            except IOError,e:
                Utils.log("Failed to modify user file %s: %s" % (user_config, str(e)))
                return False
        return True
    except IOError,e:
        Utils.log("Failed to open volume file %s: %s" % (volumeFile, str(e)))
        return False

def writeVolumeCifsSharedConfiguration(volumeName, allowhosts):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    try:
        fp = open(volumeFile, "w")
        fp.write("[%s]\n" % volumeName)
        fp.write("   comment = %s volume served by Gluster\n" % volumeName)
        fp.write("   path = %s/%s\n" % (Globals.CIFS_EXPORT_DIR, volumeName))
        fp.write("   guest ok = yes\n")
        fp.write("   browseable = yes\n")
        fp.write("   writable = yes\n")
        fp.write("   allow hosts = %s\n" % (allowhosts))
        fp.write("   create mode = 0766\n")
        fp.write("   directory mode = 0777\n")
#  #######  junlili - modified smbconf file  #########
#  ###############
        fp.close()
        return True
    except IOError, e:
        Utils.log("Failed to write file %s: %s" % (volumeFile, str(e)))
        return False


#  2012-03-22 junlili - modified this function, add several arguments
#def writeVolumeCifsConfiguration(volumeName, userList, adminUser=None):
def writeVolumeCifsConfiguration(volumeName, owner, allowhosts):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    try:
        fp = open(volumeFile, "w")
        fp.write("[%s]\n" % volumeName)
        fp.write("   comment = %s volume served by Gluster\n" % volumeName)
        fp.write("   path = %s/%s\n" % (Globals.CIFS_EXPORT_DIR, volumeName))
        fp.write("   guest ok = yes\n")
        fp.write("   public = yes\n")
        fp.write("   writable = yes\n")
#  #######  junlili - modified smbconf file  #########
        fp.write("   admin users = %s\n" % (owner))
        fp.write("   valid users = %s\n" % (owner))
        fp.write("   allow hosts = %s\n" % (allowhosts))
        fp.write("   forceuser = %s\n" % (owner))
#  ###############
#  ####### liub     - modified smbconf file  #########
        fp.write("   browseable  = no\n")
        filepath="   include=/etc/glustermg/volumes/users/%s-%s.smbconf\n"% (volumeName,"%U")
        fp.write(filepath)
#################################################
        fp.close()
    except IOError, e:
        Utils.log("Failed to write file %s: %s" % (volumeFile, str(e)))
        return False

#  ####### liub     - modify user's smbconf  #########
    try:
        if not os.path.exists("/etc/glustermg/volumes/users"):
            os.mkdir("/etc/glustermg/volumes/users")
        user_config="/etc/glustermg/volumes/users/%s-%s.smbconf"%(volumeName,str(owner))
        fp=open(user_config,'w')
        fp.write("   browseable  = yes\n")
        fp.close()
        return True
    except IOError,e:
        Utils.log("Failed to write file %s: %s" % (user_config, str(e)))
        return False
#  ######

def removeVolumeCifsConfiguration(volumeName):
    volumeFile = "%s/%s.smbconf" % (Globals.VOLUME_CONF_DIR, volumeName)
    try:
        modify_config=modifyUsersConfig(volumeName)
        if modify_config is False:
            return False
        os.remove(volumeFile)
        return True
    except OSError, e:
        Utils.log("Failed to remove file %s: %s" % (volumeFile, str(e)))
        return False

def isExecSucess(status, output, serverName, volumeName, cmd, cmdcode, params):
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        msg = 'volume {0} does not exist'
        params=[]
        params.append(volumeName)
        result = Utils.errorCode('20053', msg, params)
        raise web.HTTPError(status='400 Bad Request', data=result) 
    if status == -1:
        code, reval = '26104', 'error when connecting to remote host {0} from localhost:{1}'
    elif status == -2:
        code,reval = '26059', 'Error when using pub key to connect remote server {0}.{1}'
    elif status == 1:
        code, reval = cmdcode, 'Error when executing {0}\n{1}'
    if status:
        params=[]
        params.append(serverName)
        params.append(output)
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "500 Internal Server Error", data = result)

def startVolume(serverName, volumeName, force = False):
    cmd = 'gluster volume start ' + volumeName
    params = []
    if force:
        cmd += ' force'
    status,output = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist') or (list[-1] == 'exist\n'):
        params = []
        params.append(volumeName)
        result = Utils.errorCode('20053', 'volume {0} does not exist.\n', params)
        raise web.HTTPError(status = '400 Bad Request', data = result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23130', params)
    web.HTTPError(status='200 OK', data='')

def stopVolume(serverName, volumeName, force = False):
    cmd = 'gluster --mode=script volume stop ' + volumeName
    params = []
    if force:
        cmd += ' force'
    status,output = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    isExecSucess(status, output, serverName, volumeName, cmd, '23131', params)
    web.HTTPError(status='200 OK', data='')

def logRotate(serverName, volumeName, force = False):
    cmd = 'gluster  volume log rotate ' + volumeName
    params = []
    if force:
        cmd += ' force'
    status,output = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    isExecSucess(status, output, serverName, volumeName, cmd, '23132', params)
    web.HTTPError(status='200 OK', data='')

def rebalanceStop(serverName, volumeName, force=False):
    cmd = 'gluster volume rebalance ' + volumeName + ' stop'
    if force:
        cmd += ' force'
    status,output = Utils.executeOnServer(serverName, cmd)
    params = []
    list = output.split(' ')
    if (list[-1] == 'exist') or (list[-1] == 'exist\n'):
        params.append(volumeName)
        result = Utils.errorCode('20053', 'volume {0} does not exist.\n', params)
        raise web.HTTPError(status = '400 Bad Request', data = result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23133', params)
    web.HTTPError(status='200 OK', data='')

def rebalanceStart(clusterName, serverName, volumeName, fixLayout = False, migrateData = False, forcedDataMigrate = True, force = False):
    (status,output) = Utils.rebalanceTaskStart(clusterName, volumeName)
    if status != 0:
        return output
    params = []
    cmd = 'gluster volume rebalance ' + volumeName
    if (fixLayout == True) and (migrateData == True):
        cmd += ' start'
    elif fixLayout == True:
        cmd += ' fix-layout start'
    else:
        cmd += ' start'
    if force == True:
        cmd += 'force'
    status,output = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist') or (list[-1] == 'exist\n'):
        params.append(volumeName)
        result = Utils.errorCode('20053', 'volume {0} does not exist.\n', params)
        raise web.HTTPError(status = '400 Bad Request', data = result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23134', params)
    web.HTTPError(status='200 OK', data='')


def preCreateVolume(data):
    if len(data) == 0:
        return 'clusterName is required'
    code = None
    count = None
    try:
        volumeName = data.volumeName
        volumeType = data.volumeType
        transportType = data.transportType
        if data.replicaCount != '0':
            count = data.replicaCount
        if data.stripeCount != '0':
            count = data.stripeCount
# # #            accessProtocols = data.accessProtocols
        options = data.options
        bricks = data.bricks
        nasProtocols = data.accessProtocols
        if 'CIFS' in nasProtocols:
            isShared = data.isShared
            owner = data.owner
    except Exception,e:
        params = []
        params.append(str(e))
        result = Utils.errorCode('20001', 'paramters are required {0}', params)
        raise web.HTTPError(status = '400 Bad Request', data = result)
#          ################################## get servers in the cluster to create a volume
    ##################################set args for gluster command

    if volumeType.lower() not in VOLUME_TYPE_STR:
        code,reval = '23001', 'invalid volume type'
    if count is not None:
        try:
            count_int = int (count)
            if (count_int < 0) or (count_int == 0):
                code,reval = '23002','invalid count'
        except:
            code,reval = '23002','invalid count'
    if code is not None:
        result = Utils.errorCode(code,reval,[])
        raise web.HTTPError(status = '400 Bad Request', data = result)

    if volumeType.lower() == "replicate" or volumeType.lower() == "distributed replicate":
        volumeType = "replica"
    elif volumeType.lower() == "stripe" or volumeType == "distributed stripe":
        volumeType = "stripe"
#    elif volumeType.lower() == 'distributed replicate':

#    elif volumeType.lower() == 'distributed stripe':

    else:
        volumeType = ''
    if transportType.upper() == "ETHERNET":
        transportType = "tcp"
    else:
        transportType = "rdma"
    bricklist = bricks.split(',')
    cmd = 'gluster volume create ' + volumeName + ' '
    if (volumeType is not None) and (volumeType.strip() != ''):
        if volumeType.lower() != 'distribute':
            cmd += volumeType + ' '
            if count is not None:
                cmd += str(count)
            else:
                cmd += '2' 
    cmd += ' transport ' + transportType
    bricklist = convertToIPAddr(bricklist)
    for brickDir in bricklist:
        cmd += " " + brickDir
    return cmd, options, volumeName

def postDelete(volumeName, brickList,deleteFlag = False):
    params = []
    params.append(volumeName)
    params.append(brickList)
    params.append(deleteFlag)
    for brick in brickList:
        if brick.strip() is '':
            continue
        cmd = 'python ' + BACKEND_SCRIPT + 'clear_volume_directory.py'
        server_dir = brick.split(":/")
        if len(server_dir) != 2:
            break
        cmd += ' /' + server_dir[1].strip()
        status,output = Utils.executeOnServer(server_dir[0].strip(), cmd)
        if status == -1:
            params = []
            params.append(volumeName)
            params.append(server_dir[0].strip())
            params.append(output)
            code, reval = '26104', 'Volume {0} deleted from cluster, however following error(s) occurred:\nerror when connecting to remote host {1} from localhost:{2}'
        elif status == -2:
            code,reval = '26059', 'Volume {0} deleted from cluster, however following error(s) occurred:\nError when using pub key to connect remote server {1}.{2}'
        elif status == 1:
            if re.match('exist', output) or re.match('exists', output) or re.match('exist\n',output):
                code, reval = '20053', 'volume {0}  does not exist.\n'
            else:
                code, reval = '23101', 'Volume {0} deleted from cluster on server {1}, however following error(s) occurred:\n{2}'
        if status:
            result = Utils.errorCode(code, reval, params)
            raise web.HTTPError(status = "500 Internal Server Error", data = result)
    return ''

def postDeleteTask(clusterName, volumeName):
    params=[]
    params.append(volumeName)
    try:
        rebalanceTasks = Globals.db.select('task_info', what = '*', where = 'operation_id=3')
        for rebalanceTask in rebalanceTasks:
            if rebalanceTask.reference.strip() == volumeName.strip():
                Globals.db.delete('task_info', where = 'id=$rebalanceTask.id', vars=locals())
    except Exception,e:
        code, reval = '23222', 'volume {0} deleted, but error occured when removing rebalance tasks'
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "500 Internal Server Error", data = result)
    try:
        migrateTasks = Globals.db.select('task_info', what = '*', where = 'operation_id=2')
        for migrateTask in migrateTasks:
            if migrateTask.reference.strip().split('#')[0] == volumeName.strip():
                Globals.db.delete('task_info', where = 'id=$migrateTask.id', vars=locals())
    except Exception,e:
        code, reval = '23222', 'volume {0} deleted, but error occured when removing rebalance tasks'
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "500 Internal Server Error", data = result)
    return ''

def convertToIPAddr(brickList):
    brklist = []
    for brick in brickList:
        server_dir = brick.split(':')
        if len(server_dir) < 2:
            continue
        ip = Utils.getIPByName(server_dir[0])
        brklist.append(ip + ':' + server_dir[1])
    return brklist
