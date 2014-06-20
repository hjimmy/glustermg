import web
import os
import sys
import commands
import re
import logging
import logging.config

p1 = os.path.abspath(os.path.dirname(sys.argv[0]))

if not p1 in sys.path:
    sys.path.append(p1)

p3 = "%s/../scripts/backend" % (p1)
if not p3 in sys.path:
    sys.path.append(p3)
p4 = "%s/../scripts/common" % (p1)
if not p4 in sys.path:
    sys.path.append(p4)

import get_volume_log_message

import Utils
from VolumeUtils import *
from CifsUtils import *
from Globals import *
from XmlHandler import *
import xml.etree.ElementTree as ET
  
#db = web.database(dbn='mysql', db='webpy', user='gluster', pw='qwe123')
import serverService

logging.config.fileConfig(Globals.LOG_CONF)
logger = logging.getLogger("Volume")
'''
logger.debug("debug message")
logger.info("info message")
logger.warn("warn message")
logger.error("error message")
logger.critical("critical message")
'''

def getServerName(clusterName):
    params=[]
    if clusterName is None:
        result = Utils.errorCode('20002', 'clusterName is required', params)
        logger.error("Get serverName: clusterName is null")
        raise web.HTTPError(status = '400 Bad Request', data = result)
    status, cluster_id, servers = serverService.get_servers(clusterName)
    code = None
    if status == '-1':
        code, reval = '20052', 'No cluster {0}.'
    if status == '-2':
        code, reval = '20054', 'No server in cluster {0}.'
    if code is not None:
        params.append(clusterName)
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    for server in servers:
        if Utils.isOnline(server.name):
            return server.name.strip()
    logger.error("There is no Online Server in cluster[" + clusterName + "]")
    params.append(clusterName)
    result = Utils.errorCode('22008', 'There is no Online Server in cluster {0}', params)
    raise web.HTTPError(status = '400 Bad Request', data = result)

def removeVolume(clusterName,volumeName):
    ################################## get servers in the cluster to create a volume
    serverName = getServerName(clusterName)
    volumeInfo = getVolume(clusterName, volumeName)

    # if enableCifs is true, then stop and delete it's cifs configure first
    root = ET.fromstring(volumeInfo)
    enableCifs = "false"
    for subnode in root.getchildren():
        if subnode.tag == "enableCifs":
            enableCifs = subnode.text
        if subnode.tag == "status":
            status = subnode.text
    if enableCifs == "true":
        if status == "ONLINE":
            params = []
            params.append(volumeName)
            result = Utils.errorCode('23101', 'Volume ' + volumeName + ' has been started.Volume needs to be stopped before deletion.', params)
            logger.error('Volume ' + volumeName + ' has been started.Volume needs to be stopped before deletion.')
            raise web.HTTPError(status = '400 Bad Request', data = result)
        if not deleteVolumeCIFSUser(volumeName):
            params = []
            params.append(volumeName)
            result = Utils.errorCode('23204', 'failed to delete cifs configuration while deleting volume: ' + volumeName,params)
            logger.error("failed to delete cifs configuration while deleting volume: " + volumeName)
            raise web.HTTPError(status = '400 Bad Request', data = result)

    cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_bricks.py  ' + volumeName
    (status,output) = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        params = []
        params.append(volumeName)
        result = Utils.errorCode('20053', 'volume {0} does not exist', params)
        logger.error("Remove volume: volume[" + volumeName + "] does not exist")
        raise web.HTTPError(status='400 Bad Request', data=result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23019',[])
    ################################## prepare the command
    brickList = output.split('\n')
    cmd = 'gluster --mode=script volume delete ' + volumeName
    ################################## execute on remote host or local host
    status,output = Utils.executeOnServer(serverName, cmd)
    params = []
    params.append(clusterName)
    params.append(volumeName)
    isExecSucess(status, output, serverName, volumeName, cmd, '23101', params)
    deleteFlag = False

    postDelete(volumeName, brickList,deleteFlag)

    try:
        postDeleteTask(clusterName, volumeName)
    except:
        code, reval = '23101', 'Volume ' + volumeName +' deleted from cluster, however following error(s) occurred:\n' + output
        if status:
            result = Utils.errorCode(code, reval, params)
            logger.error(reval)
            raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        Globals.db.delete('volume_info',where='name=$volumeName', vars=locals())
    except Exception,e:
        result = Utils.errorCode('23101','error while deleting volume from DB',parseString)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def getVolume(clusterName,volumeName):
    serverName = getServerName(clusterName)
    message = Globals.mc.get(str(volumeName)+'_volume')
    dom = ResponseXml()
    if (message is not None) and (message.strip()!='<response/>'):
        logger.info("Get volume info from memcache:" + message)
        return message.replace('<?xml version="1.0" ?>','')
    cmd = "python " + BACKEND_SCRIPT + "get_volumes.py " + volumeName
    (status,output) = Utils.executeOnServer(serverName, cmd)
    isExecSucess(status, output, serverName, volumeName, cmd, '23014', [])
    dom.parseString(output)
    fetchVolumeCifsUsers(dom)
    output = dom.toxml().replace('<?xml version="1.0" ?>','').replace('<response/>','')
    Globals.mc.set(str(volumeName)+'_volume',output)
    logger.info("Get volume info by get_volumes.py:" + output)
    return output

def getVolumes(clusterName, details='false'):
    serverName = getServerName(clusterName)
    result = ''
    clusterid = Globals.db.select('cluster_info', where = 'name=$clusterName',what='*',vars=locals())
    clusterid = clusterid[0].id
    volumes = Globals.db.select('volume_info',where = 'cluster_id=$clusterid',vars=locals())
    if len(volumes) == 0:
        web.HTTPError(status='200 OK')
        logger.info("Get volumes info: null")
        return '<volumes></volumes>'
    if details.lower() != 'true':
        responseDom = ResponseXml()
        volumesTag = responseDom.createTag("volumes")
        for v in volumes:
            volumeTag = responseDom.createTag("volume")
            volumeTag.appendChild(responseDom.createTag("name",str(v.name).strip()))
            volumeTag.appendChild(responseDom.createTag("id",str(v.id).strip()))
            volumesTag.appendChild(volumeTag)
        web.HTTPError(status='200 OK')
        web.header('Content-Type','application/xml') 
        return volumesTag.toxml()
    for v in volumes:
        volumeName = str(v.name)
        if volumeName.strip()!='':
            try:
                result += getVolume(clusterName, volumeName)
            except Exception,e:
                pass
    web.HTTPError(status = "200 OK")
    web.header('Content-Type','application/xml') 
    logger.info("Get volumes info -- 200 OK")
    return '<volumes>' + result.replace('\n','').replace('<?xml version="1.0" ?>','') + '</volumes>'

def createVolume(clusterName,data):
    serverName = getServerName(clusterName)
    cmd, options, volumeName = preCreateVolume(data)
    volume_info = Globals.db.select('volume_info', what='*', where='name=$volumeName', vars=locals())
    if len(volume_info) > 0:
        params = []
        params.append(volumeName)
        result = Utils.errorCode('23015','error while adding a volume:volume ' + volumeName + ' already exists', params)
        logger.error('error while adding a volume:volume ' + volumeName + ' already exists')
        raise web.HTTPError(status = "400 Bad Request", data = result)
    #################################execute on localhost or remote host
    status,output = Utils.executeOnServer(serverName, cmd)
    if status == -1:
        code, reval = '26104', 'error when connecting to remote host ' + serverName + ' from localhost:' + output
    elif status == -2:
        code,reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + output
    elif status == 1:
        if re.match('exists', output):
            code, reval = '20103', output
        else:
            code, reval = '23015', 'Error when creating volume' + volumeName + '.' + output
    if status:
        result = Utils.errorCode(code, reval, [])
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)

    optionToken = options.split(",")
    hostAllowed = "\*"
    for option in optionToken:
        if option.split("=")[0] == "auth.allow":
            hostAllowed = option.split("=")[1]

    nasProtocols = data.accessProtocols
    if "CIFS" in nasProtocols:
        isShared = data.isShared
        owner = data.owner
        if not createVolumeCIFSUsers(volumeName, isShared, owner, hostAllowed):
            params = []
            params.append(volumeName)
            result = Utils.errorCode('23201', 'failed to configure cifs for volume: %s' % volumeName, params)
            Utils.executeOnServer(serverName, 'gluster --mode=script volume delete ' + volumeName)
            logger.error("failed to configure cifs for volume:" + volumeName) 
            raise web.HTTPError(status = '400 Bad Request',data = result)
    try:
        cluster = Globals.db.select('cluster_info',where='name=$clusterName',vars=locals())
        clusterid=cluster[0].id
        Globals.db.insert('volume_info',name=volumeName,cluster_id=clusterid)
    except:
        params = []
        params.append(volumeName)
        result = Utils.errorCode('23015','error while adding a volume:error while inserting volume_info into DB', params)
        deleteVolumeCIFSUser(volumeName)
        Utils.executeOnServer(serverName, 'gluster --mode=script volume delete ' + volumeName)
        #postDelete(volumeName, brickList,deleteFlag)
        logger.error('error while adding a volume:error while inserting volume_info into DB')
        raise web.HTTPError(status = '400 Bad Request',data = result)
    return None

def manageVolume(clusterName,volumeName,data):
    serverName = getServerName(clusterName)
    if len(serverName) == 0:
        return "No server: "+'"'+serverName+'"'
    if len(data) == 0:
        return 'operation is required'            
    ############### parameters of managin a volume
    operation = ''
    force = False ### false by defult

    ############### for rebalance
    fixLayout = False ###false by default
    migrateData = True  ### true by default
    forcedDataMigrate = False ### false by default 
    try:
        operation = str(data.operation).strip()
    except Exception,e:
        result = Utils.errorCode('20001', 'paramters are required\n' + str(e),[])
        raise web.HTTPError(status = '400 Bad Request', data = result)
                
    try:
        if data.force.lower() == 'true' :
            force = True
    except Exception,e:
        pass
                
    if (operation != 'start') and (operation != 'stop') and (operation != 'cifsConfig')\
        and (operation != 'rebalanceStart') and (operation != 'rebalanceStop') and (operation != 'logRotate'):
        params = []
        params.append(operation)
        result = Utils.errorCode('23007', 'invalid operations', params)
        raise web.HTTPError(status = '400 Bad Request', data = result)
                
    if operation == 'cifsConfig':
        try:
            isShared = data.isShared
            owner = ''
            if isShared == "false":
                owner = data.owner
            hostAllowed = '\*'
            if data.hostAllowed is not None:
                hostAllowed = data.hostAllowed
        except Exception,e:
            pass
        if not updateVolumeCIFSUsers(volumeName, isShared, owner, hostAllowed):
            params = []
            params.append(volumeName)
            result = Utils.errorCode('23135', 'failed to update cifs configure for volume: %s' % volumeName, params)
            raise web.HTTPError(status = '400 Bad Request',data = result)
        return None

    if operation == 'rebalanceStop':
        rebalanceStop(serverName, volumeName, force)
        return None
    elif operation == 'rebalanceStart':
        try:
            if data.fixLayout.lower() == 'true':
                fixLayout = True
        except Exception,e:
            pass
        try:
            if data.migrateData.lower() == 'false':
                migrateData = False
        except Exception,e:
            pass
        try:
            if data.forcedDataMigrate.lower() == 'true':
                forcedDataMigrate = True
        except Exception,e:
            pass
        rebalanceStart(clusterName, serverName, volumeName, fixLayout, migrateData, forcedDataMigrate, force)                   
        return None
    elif operation == 'start':
        startVolume(serverName, volumeName, force)
        ## If enableCifs is true, then start its export
        volumeInfo = getVolume(clusterName, volumeName)
        root = ET.fromstring(volumeInfo)
        enableCifs = "false"
        for subnode in root.getchildren():
            if subnode.tag == "enableCifs":
                enableCifs = subnode.text
        if enableCifs == "true":
            if not startCifsReExport(volumeName, serverName):
                params = []
                params.append(volumeName)
                result = Utils.errorCode('23202', 'failed to start cifs reexport for volume: ' + volumeName, params)
                raise web.HTTPError(status = '400 Bad Request',data = result)
        return None
    elif operation == 'stop':
        ## If enableCifs is true, then stop its reexport
        volumeInfo = getVolume(clusterName, volumeName)
        root = ET.fromstring(volumeInfo)
        enableCifs = "false"
        for subnode in root.getchildren():
            if subnode.tag == "enableCifs":
                enableCifs = subnode.text
        if enableCifs == "true":
            if not stopCifsReExport(volumeName):
                params = []
                params.append(volumeName)
                result = Utils.errorCode('23203', 'failed to stop cifs reexport for volume: ' + volumeName, params)
                raise web.HTTPError(status = '400 Bad Request',data = result)

        stopVolume(serverName, volumeName, force)
        return None
    else:
        logRotate(serverName, volumeName, force)
        return None

def getLogs(clusterName, volumeName):
    severity = ''
    brickName = ''
    fromTimeStamp = ''
    toTimeStamp = ''
    lineCount = ''
                
    data = web.input()
    if len(data) == 0:#return 'line count is required\n'
        pass
    try:
        lineCount = data.lineCount
    except:
        lineCount = 100 
    try:
        severity = data.severity
    except:
        severity = 'ALL' 
    try:
        brickName = data.brickName
    except:
        pass
    try:
        fromTimeStamp = data.fromTimeStamp
        toTimeStamp = data.toTimeStamp
    except:
        pass
    if brickName.strip() is '' or brickName is None:
        brickName = ' '
    ################ execute cmd on local host or remote host
    output = get_volume_log_message.getLogs(clusterName, volumeName, brickName, lineCount, severity, fromTimeStamp, toTimeStamp) #@Undefined variable
    if output.strip() == '':
        return '<logMessages></logMessages>'
    return output
       
def getOptions(clusterName, volumeName):
    serverName = getServerName(clusterName)
    cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_options.py ' + volumeName
                ################ execute cmd on local host or remote host
    (status,output) = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        result = Utils.errorCode('20053', 'volume ' + volumeName + ' does not exist', [])
        raise web.HTTPError(status='400 Bad Request', data=result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23016', [])
    return output

def setOptions(clusterName, volumeName):
    serverName = getServerName(clusterName)
    data = web.input()
    key = None
    value = None
    try:
        key = data.key.strip()
        value = data.value.strip()
    except Exception,e:
        result = Utils.errorCode('20001', 'key and value are required')
        raise web.HTTPError(status = '400 Bad Request', data = result)
    params = []
    params.append(key)
    params.append(value)
    cmd = 'gluster volume set ' + volumeName + ' ' + key + ' "' + value +'"'
    (status,output) = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        result = Utils.errorCode('20053', 'volume ' + volumeName + ' does not exist', params)
        raise web.HTTPError(status='400 Bad Request', data=result)
    isExecSucess(status, list[0], serverName, volumeName, cmd, '23017', params)
    return ''

def resetOptions(clusterName, volumeName):
    serverName = getServerName(clusterName)
    cmd = 'gluster volume reset ' + volumeName
    (status,output) = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        result = Utils.errorCode('20053', 'volume ' + volumeName + ' does not exist', [])
        raise web.HTTPError(status='400 Bad Request', data=result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23018',[])
    return ''

def downloadLogs(clusterName, volumeName):
    params = []
    web.header('Content-Type','application/octet-stream')
    serverName = getServerName(clusterName)
    hostName = os.popen('hostname').read()
    cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_bricks.py  ' + volumeName
    (status,output) = Utils.executeOnServer(serverName, cmd)
    list = output.split(' ')
    if (list[-1] == 'exist\n') or (list[-1] == 'exist'):
        params.append(volumeName)
        result = Utils.errorCode('20053', 'volume ' + volumeName + ' does not exist', params)
        raise web.HTTPError(status='400 Bad Request', data=result)
    isExecSucess(status, output, serverName, volumeName, cmd, '23019',[])
    
    bricklist = output.split('\n')
    if status != 0:
        return output
    result = ''
    if os.path.exists(TMP_LOG_DIR) == False:
        os.mkdir(TMP_LOG_DIR)
    logs = ''
    for brick in bricklist:
        server_dir = brick.split(':/')
        if len(server_dir) != 2:
            break
        file = server_dir[1].strip()
        log = file.replace('/', '-') + '.log'
        status,files = Utils.executeOnServer(server_dir[0].strip(),'ls ' + BRICK_LOG_DIR +'|grep ^' + log)
        files = files.split('\n')
        for file in files:
            if file.strip() is '':
                break
            cmd = 'scp ' + str(BRICK_LOG_DIR) + str(file) + \
            ' root@' + str(hostName).strip().split('\n')[0] + \
            ':' + TMP_LOG_DIR + '/' + str(server_dir[0].strip()) + '-' + file
            (status,output) = Utils.executeOnServer(server_dir[0].strip(), cmd)
            logs += ' ' + server_dir[0].strip() + '-' + file
            if output[:7] == 'Warning':
                continue
            isExecSucess(status, output, serverName, volumeName, cmd, '23019', [])
            
    if os.path.exists(TMP_LOG_DIR + volumeName + '.tar.gz'):
        os.remove(TMP_LOG_DIR + volumeName + '.tar.gz')
    os.chdir(TMP_LOG_DIR)
    log = TMP_LOG_DIR + volumeName + '.tar.gz'
    if os.path.exists(log):
        os.remove(log)
    os.popen('tar cvzf ' + volumeName + '.tar.gz ' + logs)
    os.popen('rm -rf ' + logs)
    try:
	f=open(volumeName+'.tar.gz')
        stream = f.read()
    except Exception,e:
        params.append(volumeName)
        result = Utils.errorCode('23019', 'error when downloading logs', params)
        raise web.HTTPError(status='500 Internal Error', data=result)
    return stream
