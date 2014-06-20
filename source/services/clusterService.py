###added by jian.hou cluster operations
import web
import logging
import logging.config
from decimal import *
from scripts.common import Globals, Utils, VolumeUtils, Thread, XmlHandler
from services import taskService
import xml.etree.ElementTree

db = Globals.db
logging.config.fileConfig(Globals.LOG_CONF)
logger = logging.getLogger("Cluster")
'''
logger.debug("debug message")
logger.info("info message")
logger.warn("warn message")
logger.error("error message")
logger.critical("critical message")
'''

def getClusters():
    try:
        responseDom = XmlHandler.ResponseXml()
        clustersTag = responseDom.appendTagRoute("clusters")
        clustersNameList = db.select('cluster_info')
        clustersNameList1 = []
        if len(clustersNameList) == 0:
            logger.info("Get clusters list :" + str(clustersNameList1))
            return '<clusters></clusters>'
        for cluster in clustersNameList:
            clustersTag.appendChild(responseDom.createTag("cluster", cluster.name))
            clustersNameList1.append(str(cluster.name))
        logger.info("Get clusters list :" + str(clustersNameList1))
        return clustersTag.toxml()
    except Exception, e:
        code,reval = "21008", "Error when getting clusters info: " + str(e) 

    logger.error(reval)
    result = Utils.errorCode(code, reval, [])
    raise web.HTTPError(status = "400 Bad Request", data = result)

def createCluster():
    try:
        data = web.input() 
        clusterName = data.clusterName
        cluster_info = db.select('cluster_info',where='name=$clusterName' ,what="id",vars=locals())
        if len(cluster_info) != 0:
            code, reval = "20102", "Error when creating a cluster: "+clusterName+" has already exisited"
        else:
            db.insert('cluster_info',name=clusterName)
            logger.info("Create cluster[" + clusterName + "] successfully!")
            return ''
    except Exception, e:
        code, reval = "21005", "Error when creating a cluster:" + str(e)

    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def registerCluster():
    try:
        data = web.input()
        clusterName = data.clusterName
        serverName = data.serverName
        cluster_info = db.select('cluster_info',where='name=$clusterName' ,what="id",vars=locals())
        if len(cluster_info) != 0:
            code, reval = "20102", "Error "+clusterName+" has already existed"
        else:
            server_info = db.select('server_info',where='name=$serverName' ,what="id",vars=locals())
            if len(server_info) != 0:    
                code, reval = "20104", "Error "+serverName+" has already existed"
            else:
                cluster_id = db.insert('cluster_info',name=clusterName)
                db.insert('server_info',name=serverName,cluster_id=cluster_id)
                logger.info("Register cluster[" + clusterName + "] with server[" + serverName +"] successfully!")
                return ''
    except Exception, e:
        code, reval = "21002", "Error when registering a cluster:" + str(e)

    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(serverName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def unregisterCluster(clusterName):
    try:
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20200", "Error +["+clusterName+"] not exisit"
        else:
            cluster_id = cluster_id_info[0].id
            db.delete('cluster_info',where='name=$clusterName', vars=locals())
            db.delete('server_info',where='cluster_id=$cluster_id',vars=locals())
            logger.info("Unregister cluster[" + clusterName + "] successfully!")
            return ''
    except Exception,e:
        code, reval = "21004", "Error when  unregistering a cluster:" + str(e)

    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def initCluster(clusterName):
    try:
        images = ""
        vms = ""
        vars = ""
        params = []
        params.append(clusterName)
        cluster_id_info = db.select('cluster_info',where='name=$clusterName' ,what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20200", "Error "+clusterName+" not existed"
            raise ClusterException(code,reval,params)
        data = web.input()
        dirs = data.dirs
        data_info = dirs.split(',')
        count = 0
        for dir in data_info:
            mkdir = dir.split(':')
            commandWithArgs = "mkdir -p " + mkdir[1]
            status,message = Utils.executeOnServer(mkdir[0],commandWithArgs)
            images = images + dir + "/neofs-images "
            vms = vms + dir + "/neofs-vms "
            vars = vars + dir + "/var-images "
            count = count + 1
        if count % 2 != 0:
            code, reval = "21006", "the number of dirs is must be a multiple of 2"
            raise ClusterException(code,reval,params)
        cluster_id = cluster_id_info[0].id
        servers = getOnlineServer(cluster_id)
        serverName = servers[0]
        commandWithArgs = "gluster volume --mode=script create neofs-images replica 2 " + images
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21007", "Error when create volume [neofs-images]: "+message
            raise ClusterException(code,reval,params)
        db.insert('volume_info',name="neofs-images",cluster_id=cluster_id)
        commandWithArgs = "gluster volume --mode=script create neofs-vms replica 2 " + vms
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21008", "Error when create volume [neofs-vms]: "+message
            raise ClusterException(code,reval,params)
        db.insert('volume_info',name="neofs-vms",cluster_id=cluster_id)
        commandWithArgs = "gluster volume --mode=script create var-images replica 2 " + vars
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21009", "Error when create volume [var-images]: "+message
            raise ClusterException(code,reval,params)
        db.insert('volume_info',name="var-images",cluster_id=cluster_id)
        commandWithArgs = "gluster volume --mode=script start neofs-images "
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21010", "Error when start volume [neofs-images]: "+message
            raise ClusterException(code,reval,params)
        commandWithArgs = "gluster volume --mode=script start neofs-vms "
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21011", "Error when start volume [neofs-vms]: "+message
            raise ClusterException(code,reval,params)
        commandWithArgs = "gluster volume --mode=script start var-images "
        status,message = Utils.executeOnServer(serverName,commandWithArgs)
        if status != 0:
            code, reval = "21012", "Error when start volume [var-images]: "+message
            raise ClusterException(code,reval,params)
        server_name_info = db.select('server_info',where='cluster_id=$cluster_id' ,what="name",vars=locals())
        for server in server_name_info:
            serverName = server.name
            commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_setup.sh " + serverName
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
        db.update('cluster_info', where="name = $clusterName", init = '1' ,vars=locals())
        logger.info("Init cluster[" + clusterName + "] successfully!")
        return ''
    except ClusterException,e:
        logger.error(e.reval)
        errorreturn (e.code,e.reval,e.params)
    except Exception, e:
        code, reval = "21013", "Error when initialize a cluster:" + str(e)
 
    logger.error(reval)
    errorreturn(code,reval,params)

class ClusterException(Exception):
    def __init__(self,code,reval,params):
        Exception.__init__(self)
        self.code = code
        self.reval = reval
        self.params = params

def errorreturn(code,reval,params):
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def getOnlineServer(cluster_id):
    server_name_info = db.select('server_info',where='cluster_id=$cluster_id' ,what="name",vars=locals())
    servers = []
    for server in server_name_info:
        if Utils.isOnline(server.name) == True:
            serverName = server.name
            servers.append(serverName.strip())
    return servers

def operationCluster(clusterName):
    try:
        cluster_id_info = db.select('cluster_info',where='name=$clusterName' ,what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20200", "Error ["+clusterName+"] not existed"
        else:
            data = web.input()
            operation = data.operation
            status,local_IP = Utils.getLocal_IP()
            localIP =  local_IP.strip()
            cluster_id = cluster_id_info[0].id
            server_name_info = db.select('server_info',where='cluster_id=$cluster_id' ,what="name",vars=locals())
            if operation == "mount":
                for server in server_name_info:
                    serverName = server.name
                    commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_setup.sh " + serverName
                    status,message = Utils.executeOnServer(serverName,commandWithArgs)
                    if status != 0:
                        code, reval = "21015", "Error when operation[mount] cluster[" + clusterName + "]: mount failure on server[" + serverName + "]"
                        break
                if status == 0:
                    logger.info("Operation[mount] cluster[" + clusterName + "] successfully!")
                    return ''

            elif operation == "umount":
                for server in server_name_info:
                    serverName = server.name
                    commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_teardown.sh " + serverName
                    status,message = Utils.executeOnServer(serverName,commandWithArgs)
                    if status != 0:
                        code, reval = "21015", "Error when operation[umount] cluster[" + clusterName + "]: umount failure on server[" + serverName + "]"
                        break
                if status == 0:
                    logger.info("Operation[umount] cluster[" + clusterName + "] successfully!")
                    return ''

            elif operation == "remount":
                for server in server_name_info:
                    serverName = server.name
                    commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_teardown.sh " + serverName
                    status,message = Utils.executeOnServer(serverName,commandWithArgs)
                    if status != 0:
                        code, reval = "21015", "Error when operation[remount] cluster[" + clusterName + "]: umount failure on server[" + serverName + "]"
                        break
                    commandWithArgs = "sh " + Globals.BACKEND_SCRIPT + "neofs_setup.sh " + serverName
                    status,message = Utils.executeOnServer(serverName,commandWithArgs)
                    if status != 0:
                        code, reval = "21015", "Error when operation[remount] cluster[" + clusterName + "]: mount failure on server[" + serverName + "]"
                        break
                if status == 0:
                    logger.info("Operation[remount] cluster[" + clusterName + "] successfully!")
                    return ''

            else:
                code, reval = "21014", "Error when operation cluster[" + clusterName + "]: no such operation on cluster"
    except Exception, e:
        code, reval = "21015", "Error when operation a cluster:" + str(e)

    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def getCluster(clusterName):
    try:
        online = 0
        sun = 0
        params = []
        params.append(clusterName)
        cluster_id_info = db.select('cluster_info',where='name=$clusterName' ,what="*",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20200", "Error ["+clusterName+"] not existed"
            raise ClusterException(code,reval,params)
        cluster_id = cluster_id_info[0].id
        cluster_id_info = db.select('cluster_info',where='name=$clusterName' ,what="*",vars=locals())
        init = cluster_id_info[0].init
        server_name_info = db.select('server_info',where='cluster_id=$cluster_id' ,what="name",vars=locals())
        if len(server_name_info) == 0:
            logger.info("Get cluster[" + clusterName + "] details successfully")
            return "<clusterDetail><name>" + clusterName + "</name><init>"+str(init)+"</init></clusterDetail>"
        serversInfo = getServersInfo(server_name_info,clusterName)
        tasksInfo = getTasksInfo(clusterName)
        volumesInfo = getVolumesInfo(clusterName)
        clusterXml = clusterDetailsTag(clusterName,init,serversInfo,volumesInfo,tasksInfo)
        logger.info("Get cluster[" + clusterName + "] details successfully")
        return clusterXml
    except ClusterException,e:
        logger.error(e.reval)
        errorreturn(e.code,e.reval,e.params)
    except Exception, e:
        code, reval = "21016", "Error when get a cluster details:" + str(e)

    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def getServersInfo(serverNameInfo,clusterName):
    sum = 0
    online = 0
    serversInfo = []
    servers = []
    sum = len(serverNameInfo)
    totalSpace = Decimal("0.0")
    usedSpace = Decimal("0.0")
    strs = str(clusterName) + "_servers"
    message = Globals.mc.get(strs)
    if message is not None:
        serversInfo = message
    else:
        for server in serverNameInfo:
            serverName = str(server.name)
            servers.append(serverName)
            if Utils.isOnline(serverName) == True:
                cmd = 'python ' + Globals.BACKEND_SCRIPT + 'get_server_bricks.py'
                status,message = Utils.executeOnServer(serverName, cmd)
                if status == 0:
                    if message.strip() != '[]':
                        message = message.replace("['",'')
                        message = message.replace("']",'')
                        info = message.split(':')
                        usedSpace =  usedSpace + Decimal(info[2])
                        totalSpace = totalSpace + Decimal(info[3])
            online = online + 1
        serversInfo.append(online)
        serversInfo.append(sum)
        serversInfo.append(usedSpace)
        serversInfo.append(totalSpace)
        serversInfo.append(servers)
    return serversInfo

def getTasksInfo(clusterName):
    strs =  str(clusterName) + "_tasks"
    tasksInfo = []
    message = Globals.mc.get(strs)
    print message
    if message is not None:
        return message
    tasks_sum = 0
    tasks_commit = 0
    task_info = db.select('task_info ,operation_info',where='task_info.operation_id=operation_info.id and task_info.cluster_name=$clusterName ',what = "task_info.id as taskID,description,reference,operation_id,operation_info.id,operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported",vars=locals())
    tasks_sum = len(task_info)
    if tasks_sum > 0:
        for task in task_info:
            if task.operation_id == 2:
                migrate = taskService.Migrate_operation()
                (code, reval) = migrate.get_migrate_info(task.reference)
                (code,message) = taskService.getMigrateStatus(reval)
                if code == 0:
                    tasks_commit = tasks_commit + 1
            elif task.operation_id == 1:
                disk = taskService.Disk_operation()
                (code, reval) = disk.get_disk_info(task.reference)
                messages = reval.split('\n')
                message = messages[len(messages) - 1].strip()[:-1]
                code, message = taskService.getInitialStatus(reval)
                if code == 0:
                    tasks_commit = tasks_commit + 1
            else:
                rebal = taskService.Rebalance_operation()
                (code, reval) = rebal.get_rebalance_info(task.reference)
                if code == 0:
                    tasks_commit = tasks_commit + 1
        tasksInfo = tasks_commit,tasks_sum
    return tasksInfo

def getVolumesInfo(clusterName):
    strs =  str(clusterName) + "_volumes"
    message = Globals.mc.get(strs)
    if message is not None:
        return message
    onlineNum = 0
    totalNum = 0
    volumes = []
    cluster_info = Globals.db.select('cluster_info',where='name=$clusterName',what='*',vars=locals())
    clusterid = cluster_info[0].id
    server_info = Globals.db.select('server_info', where='cluster_id=$clusterid',vars=locals())
    for server in server_info:
        if Utils.isOnline(str(server.name)) == False:
            continue
    status, message = Utils.executeOnServer(str(server.name), 'gluster volume list')
    if  message.strip() != 'No volumes present in cluster':
        volumeList = message.split('\n')
        if len(volumeList) != 0:
            onlineNum = 0
            totalNum = 0
            volumes = []
            for v in volumeList:
                if v.strip() != '':
                    cmd = "python " + Globals.BACKEND_SCRIPT + "get_volumes.py " + v
                    status,message = Utils.executeOnServer(str(server.name), cmd)
                    totalNum += 1
                    volumes.append(v)
                    if status == 0:
                        weblog = xml.etree.ElementTree.fromstring(message)
                        for entry in weblog.findall('status'):
                            status = entry.text
                        if status.strip().lower() == 'online':
                            onlineNum += 1
    clusterVolumeInfo = []
    clusterVolumeInfo.append(onlineNum)
    clusterVolumeInfo.append(totalNum)
    clusterVolumeInfo.append(volumes)
    return  clusterVolumeInfo

def clusterDetailsTag(clusterName,init,serversInfo,volumesInfo,tasksInfo):
    responseDom = XmlHandler.ResponseXml()
    clusterTag  = responseDom.appendTagRoute("clusterDetail")
    serversTag  = responseDom.appendTagRoute("servers")
    serversTag.appendChild(responseDom.createTag("online", serversInfo[0]))
    serversTag.appendChild(responseDom.createTag("sum", serversInfo[1]))
    serversTag.appendChild(responseDom.createTag("avaliableSpace", serversInfo[2]))
    serversTag.appendChild(responseDom.createTag("totalSpace", serversInfo[3]))
    for server in serversInfo[4]:
        serversTag.appendChild(responseDom.createTag("server", server))
    volumesTag  = responseDom.appendTagRoute("volumes")
    volumesTag.appendChild(responseDom.createTag("online", volumesInfo[0]))
    volumesTag.appendChild(responseDom.createTag("sum", volumesInfo[1]))
    volumesTag.appendChild(responseDom.createTag("avaliableSpace", serversInfo[2]))
    volumesTag.appendChild(responseDom.createTag("totalSpace", serversInfo[3]))
    for volume in volumesInfo[2]:
        volumesTag.appendChild(responseDom.createTag("volume", volume))
    tasksTag  = responseDom.appendTagRoute("tasks")
    if str(tasksInfo) != "[]":
        tasksTag.appendChild(responseDom.createTag("complete", tasksInfo[0]))
        tasksTag.appendChild(responseDom.createTag("sum", tasksInfo[1]))
    clusterTag.appendChild(responseDom.createTag("name", clusterName))
    clusterTag.appendChild(responseDom.createTag("init", init))
    clusterTag.appendChild(serversTag)
    clusterTag.appendChild(volumesTag)
    clusterTag.appendChild(tasksTag)
    return clusterTag.toxml()
