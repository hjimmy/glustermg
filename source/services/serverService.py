import web
import commands
import logging
import logging.config

from scripts.common import XmlHandler, Globals, Utils

logging.config.fileConfig(Globals.LOG_CONF)
logger = logging.getLogger("Server")
'''
logger.debug("debug message")
logger.info("info message")
logger.warn("warn message")
logger.error("error message")
logger.critical("critical message")
'''

def get_clusters(clusterName):
    cluster = Globals.db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
    if len(cluster) == 0:
        return '-1',None
    return '0',cluster[0].id

def get_servers(clusterName):
    status, cluster_id = get_clusters(clusterName)
    if cluster_id is None:
        return status,None,None
    server_info = Globals.db.select('server_info',where='cluster_id=$cluster_id',what="*",vars=locals())
    if len(server_info) == 0:
        return '-2',cluster_id,None
    return '0', cluster_id, server_info

def get_server(clusterName,serverName):
    status, cluster_id = get_clusters(clusterName)
    if cluster_id is None:
        return status,None,None
    server_info = Globals.db.select('server_info',where='cluster_id=$cluster_id and name=$serverName',what="id",vars=locals())
    if len(server_info) == 0:
        return '-2',cluster_id,None
    return '0',cluster_id,server_info[0].id

def getServers(clusterName, details='true'):
    code = None
    reval = None
    status,cluster_info,server_info = get_servers(clusterName)
    if status == '-1':
        code, reval = '20052', 'No cluster ' + clusterName + '.'
        result = Utils.errorCode(code, reval, [])
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    if status == '-2':
        web.HTTPError(status='200 OK')
        logger.info("Servers list is None")
        return '<servers></servers>'        
    try:
        responseDom = XmlHandler.ResponseXml()
        serversTag = responseDom.appendTagRoute('servers')
        if details.lower() != 'true':
            for server in server_info:
                glusterServerTag = responseDom.createTag('glusterServer')
                glusterServerTag.appendChild(responseDom.createTag('name', server.name))
                glusterServerTag.appendChild(responseDom.createTag('id', server.id))
                serversTag.appendChild(glusterServerTag)
                
            web.HTTPError(status='200 OK')
            logger.info("Get servers's name list - 200 OK")
            return serversTag.toxml()
        else:
            retval = ''
            cmd = 'python ' + Globals.BACKEND_SCRIPT + 'get_server_details.py 2>/dev/null'
            offline = []
            for server in server_info:
                if Utils.isOnline(server.name) == False:
                    offline.append(server.name)
                else:
                    serverName = str(server.name)
                    message = Globals.mc.get(serverName+'_server')
                    if message is not None:
                        retval += message
                    else:
                        status, message = Utils.executeOnServer(server.name, cmd)
                        if status == -1:
                            code,reval = '26104', message
                        elif status == -2:
                            code,reval = '26059', 'Error when using pub key to connect remote server ' + server.name + '.' + message
                        elif status == 1:
                            code,reval = '22002', 'error when getting details from server ' + server.name + '.' + message
                        if code is not None:
                            result = Utils.errorCode(code, reval, [])
                            web.HTTPError(status = "400 Bad Request",data='')
                            logger.error(reval)
                            return result
                        retval += message
            result = ''
            if len(offline): 
                for server in offline:
                    serverxml = '<glusterServer><name>' + server + '</name><status>OFFLINE</status></glusterServer>'
                    result += serverxml
            retval += result
            if (retval is not None) and (retval.strip() is not ''):
                web.HTTPError(status='200 OK')
                logger.info("Get servers's details info:" + retval)
                return '<servers>' + retval + '</servers>'
    except Exception,e:
        code, reval = "22002", "Error when getting servers list:" + str(e)
        result = Utils.errorCode(code, reval, [])
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def getServer(clusterName,serverName):
    status,cluster_info,server_info = get_server(clusterName,serverName)
    code = None
    reval = None
    if status == '-1':
        code,reval = '20052', "No cluster " + clusterName
    elif status == '-2':
        code,reval = '20054', 'No server ' + serverName + ' in cluster ' + clusterName
    elif Utils.isOnline(serverName) == False:
        code,reval = '22008', 'Server ' + serverName +' is not online'
    if code is not None:
        result = Utils.errorCode(code, reval, [])
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        serverName = str(serverName)
        message = Globals.mc.get(serverName+'_server')
        if message is not None:
            logger.info("Get server[" + serverName + "]'s details from memcache:" + message)
            return message
        cmd = 'python ' + Globals.BACKEND_SCRIPT + 'get_server_details.py'
        status,message = Utils.executeOnServer(serverName, cmd)
        if status == -1:
            code,reval = '26104', message
        elif status == -2:
            code,reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + message
        elif status == 1:
            code,reval = '22002', 'error when getting details from server ' + serverName + '.' + message
        if code is not None:
            result = Utils.errorCode(code, reval, [])
            logger.error(reval)
            raise web.HTTPError(status = "400 Bad Request", data = result)
        logger.info("Get server[" + serverName + "]'s details by executing get_server_details.py:" + message)
        return message
    except Exception,e:
        code, reval = "22002", "Error when getting servers list:" + str(e)
        result = Utils.errorCode(code, reval, [])
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def addServerToCluster(clusterName, data):
    code = None
    reval = None
    try:
        serverName = data.serverName
    except Exception, e:
        code, reval = "22010", "Error when getting servers list:serverName is required" + str(e)
        logger.error(reval)
        result = Utils.errorCode(code, reval, [])
        raise web.HTTPError(status = "400 Bad Request", data = result)

    status,clusterid,serverid = get_server(clusterName,serverName)
    params = []
    params.append(clusterName)
    params.append(serverName)
    if status == '-1':
        code, reval = '20052', 'No cluster ' + clusterName+'.'
    elif serverid is not None:
        code, reval = '20104', 'server ' + serverName + ' is already in cluster ' + clusterName +'.'
    elif not Utils.isOnline(serverName):
        code, reval = '22008', serverName + ' is not online.'
    if code is not None:
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        server_info = Globals.db.select('server_info',what='*',where='name=$serverName',vars=locals())
        if len(server_info) > 0:
            code, reval = "22001", "Error when adding server " + serverName + " to cluster " + clusterName + '. server ' + serverName + ' already exists.'
            web.HTTPError(status = "400 Bad Request", data = '')
            logger.error(reval)
            return Utils.errorCode(code, reval, params)
        server_info = Globals.db.select('server_info',what='*',where='cluster_id=$clusterid',vars=locals())
        if len(server_info) == 0:
            #insert into database
            status,hosts = Utils.getHosts(serverName)
            if status == -1:
                code, reval = '26104', 'error when connecting to remote host ' + serverName + ' from localhost:' + hosts
            elif status == -2:
                code, reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + hosts
            if code is not None:
                params = []
                params.append(clusterName)
                params.append(serverName)
                result = Utils.errorCode(code, hosts, params)
                web.HTTPError(status = "400 Bad Request", data = '')
                logger.error(reval)
                return result
            if status == 1 or len(hosts) == 0:
                Globals.db.insert('server_info',name=serverName,cluster_id=clusterid)
                return ''
            
            for serverName in hosts:
                try:
                    status,output = Utils.installPubKey(serverName)
                except:
                    pass
                Globals.db.insert('server_info',name=serverName,cluster_id=clusterid)
                if status is not '0':
                    web.HTTPError(status = "400 Bad Request", data = '')
                    logger.error("Error when installing pubKey on server[" + serverName + "]: " + output)
                    return Utils.errorCode(status, output, [])
            logger.info("Add the first server[" + serverName + "] to cluster[" + clusterName + "] successfully!")
            return ''
        status,output = Utils.installPubKey(serverName)
        if status is not '0':
            web.HTTPError(status = "400 Bad Request", data = '')
            logger.error("Error when installing pubKey on server[" + serverName + "]: " + output)
            return Utils.errorCode(status, output, [])
        server = server_info[0]
        status, output = Utils.executeOnServer(server.name,"gluster peer probe " + Utils.getIPByName(serverName))
        if status == -1:
            code, reval = '26104', 'error when connecting to remote host ' + serverName + ' from localhost ' + server.name + '.' + output
        elif status == -2:
            code,reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + output
        elif status == 1:
            code, reval = '22013', 'Error when executing "gluster peer probe ' + Utils.getIPByName(serverName) + '"' + output
        if code is not None:
            params = []
            params.append(clusterName)
            params.append(serverName)
            result = Utils.errorCode(code, reval, params)
            web.HTTPError(status = "400 Bad Request", data = '')
            logger.error(reval)
            return result
        Globals.db.insert('server_info',name=serverName,cluster_id=clusterid)
        logger.info("Add another server[" + serverName + "] to cluster[" + clusterName + "] successfully!")
        return ''
    except Exception,e:
        code, reval = "22001", "Error when adding server " + serverName + " to cluster " + clusterName + '.' + str(e)
        result = Utils.errorCode(code, reval, [])
        raise web.HTTPError(status = "400 Bad Request", data = result)

def removeServerFromCluster(clusterName, serverName):
    code = None
    reval = None
    params = []
    params.append(clusterName)
    params.append(serverName)
    status,clusterid,server_id = get_server(clusterName,serverName)
    if status == '-1':
        code, reval = '20052', 'No cluster ' + clusterName + '.'
    elif status == '-2':
        code, reval = '20054', 'server ' + serverName +' is not in cluster ' + clusterName
    elif Utils.isOnline(serverName) == False:
        code, reval = '22008', 'Server ' + serverName +' is not online'
    if code is not None:
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        servers = Globals.db.select('server_info',what='*',where='cluster_id=$clusterid',vars=locals())
        if len(servers) == 0:
            logger.info("This server[" + serverName + "] not contained in table server_info")
            return ''
        if len(servers) == 1:
            Globals.db.delete('server_info', where='id=$server_id', vars=locals())
            logger.info("delete server[" + serverName + "] from table server_info")
            return ''
        for server in servers:
            if (Utils.getIPByName(server.name) != Utils.getIPByName(serverName)) and (server.name.strip()!=serverName):
                break
        
        if Utils.isLocalHost(serverName):
            status,ip = Utils.getLocal_IP()
        else:
            ip = Utils.getIPByName(serverName)
        status,msg = Utils.executeOnServer(server.name,"gluster --mode=script peer detach " + ip)
        if status == -1:
            code, reval = '26104', 'error when connecting to remote host ' + serverName + ' from localhost ' + server.name + '.' + msg
        elif status == -2:
            code, reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + msg
        elif status == 1:
            code, reval = '22014', 'Error when executing "gluster --mode=script peer detach ' + ip + '"' + msg
        if code is not None:
            result = Utils.errorCode(code, reval, params)
            web.HTTPError(status = "400 Bad Request", data = '')
            logger.error(reval)
            return result
        Globals.db.delete('server_info', where='id=$server_id', vars=locals())
        return ''
    except Exception, e:
        code, reval = '22101', 'failed to remove server ' + serverName + '.' + str(e)
        logger.error(reval)
        result = Utils.errorCode(code, reval, params)
        raise web.HTTPError(status = "400 Bad Request", data = result)

def initDisk(clusterName, serverName, diskName, data):
    try:
        fsType = data.fsType
        mountPoint = data.mountPoint
    except Exception, e:
        code, reval = "22011", "Error when getting servers list:fsType and mountPoint are required." + str(e)
        logger.error(reval)
        result = Utils.errorCode(code, reval, [])
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        code = None
        reval = None
        status,clusterid,server_id = get_server(clusterName,serverName)
        if status == -1:
            code, reval = '20052', 'No cluster ' + clusterName + '.'
        elif status == -2:
            code, reval = '20054', 'server ' + serverName +' is not in cluster ' + clusterName
        if Utils.isOnline(serverName) == False:
            code, reval = '22008', 'Server ' + serverName +' is not online.'
        if code is not None:
            params = []
            params.append(clusterName)
            params.append(serverName)
            params.append(diskName)
            params.append(fsType)
            params.append(mountPoint)
            result = Utils.errorCode(code, reval, params)
            logger.error(reval)
            raise web.HTTPError(status = "400 Bad Request", data = result)
        ################### initializing the disk ####################
        initcmd = 'python ' + Globals.BACKEND_SCRIPT + 'format_device.py ' + fsType + ' "' + mountPoint + '" ' + diskName
        ################### check the status of initializing ###############
        #   chkcmd = 'python get_format_device_status.py ' + diskName
        ################### properties in the task_info table ###############
        references = serverName + ':' + diskName
        descriptions = 'Initializing Disk ' + serverName + ':' + diskName
        operationid = 1
        Globals.db.insert('task_info', reference=references, description=descriptions, operation_id=operationid, cluster_name=clusterName)
        ################### on remote or local #################
        (status, msg) = Utils.executeOnServer(serverName.strip(), initcmd)
        if status == -1:
            code, reval = '26104', 'error when connecting to remote host ' + serverName + ' from localhost:' + msg
        elif status == 1:
            code, reval = '22102', 'Error when executing format.py on server ' + serverName + '.' + msg
        elif status == -2:
            code, reval = '26059', 'Error when using pub key to connect remote server ' + serverName + '.' + msg
        if code is not None:
            params = []
            params.append(clusterName)
            params.append(serverName)
            params.append(diskName)
            params.append(fsType)
            params.append(mountPoint)
            result = Utils.errorCode(code, reval, params)
            logger.error(reval)
            raise web.HTTPError(status = "400 Bad Request", data = result)
        logger.info("Init disk[" + diskName + "] successfully!")
        return ''
    except Exception, e:
        code,reval = '22005','failed to format disk ' + diskName + ':' + str(e)
        params = []
        params.append(clusterName)
        params.append(serverName)
        params.append(diskName)
        params.append(fsType)
        params.append(mountPoint)
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    
def getDiskStatus(reference):
    server_disk = reference.split(':')
    chkcmd = 'python ' + Globals.BACKEND_SCRIPT + 'get_format_device_status.py ' + server_disk[1]

    if Utils.isLocalHost(server_disk[0].strip()):
        (status, output) = commands.getstatusoutput(chkcmd)
    else:
        (status, output) = Utils.executeOnServer(server_disk[0].strip(), chkcmd)
    return (status,output)

def operationServer(clusterName,serverName):
    code = None
    reval = None
    params = []
    params.append(clusterName)
    params.append(serverName)
    status,clusterid,server_id = get_server(clusterName,serverName)
    if status == '-1':
        code, reval = '20052', 'No cluster ' + clusterName + '.'
    elif status == '-2':
        code, reval = '20054', 'server ' + serverName +' is not in cluster ' + clusterName
    elif Utils.isOnline(serverName) == False:
        code, reval = '22008', 'Server ' + serverName +' is not online'
    if code is not None:
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        data = web.input()
        operationName = data.operation
        if operationName == "mount":
            commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_setup.sh " + serverName
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            return ''
        elif operationName== "umount":
            commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_teardown.sh " + serverName
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            return ''
        elif operationName == "remount":
            commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_teardown.sh " + serverName
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_setup.sh " + serverName
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            return ''
        else:
            return "22200", "Error no such operation on server"
    except Exception, e:
        code, reval = "22201", "Error when operation a cluster:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(serverName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def getNeofsStatus(clusterName,serverName):
    code = None
    reval = None
    params = []
    params.append(clusterName)
    params.append(serverName)
    status,clusterid,server_id = get_server(clusterName,serverName)
    if status == '-1':
        code, reval = '20052', 'No cluster ' + clusterName + '.'
    elif status == '-2':
        code, reval = '20054', 'server ' + serverName +' is not in cluster ' + clusterName + '.'
    elif Utils.isOnline(serverName) == False:
        code, reval = '22008', 'Server ' + serverName +' is not online.'
    if code is not None:
        result = Utils.errorCode(code, reval, params)
        logger.error(reval)
        raise web.HTTPError(status = "400 Bad Request", data = result)
    try:
        commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_status.sh"
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        responseDom = XmlHandler.ResponseXml()
        tasksTag = responseDom.appendTagRoute("responseStatus")
        tasksTag.appendChild(responseDom.createTag("status",message))
        logger.info("Get neofs mount status: " + message)
        return tasksTag.toxml()
    except Exception, e:
        code, reval = "22202", "Error when get neofs status on server:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(serverName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)
