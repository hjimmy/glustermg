###added by jian.hou brick operations
import web
import logging
import logging.config
from scripts.common import Globals, Utils, VolumeUtils,Thread
from services import taskService

db = Globals.db
logging.config.fileConfig(Globals.LOG_CONF)
logger = logging.getLogger("Brick")
'''
logger.debug("debug message")
logger.info("info message")
logger.warn("warn message")
logger.error("error message")
logger.critical("critical message")
'''

def addBrick(clusterName,volumeName):
    try:
        data = web.input()
        serverName,code,reval = isPathExist(clusterName,volumeName,data)
        if code == 0:
            bricks = data.bricks
            bricks = bricks.replace(' ',',')
            brickList = bricks.split(',')
            brickList = VolumeUtils.convertToIPAddr(brickList)
            bricks = ''
            for brick in brickList:
                bricks += brick + ' '
            commandWithArgs = "gluster volume add-brick " + volumeName + " " + bricks
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            if status == 0:
                logger.info("Add bricks to volume[" + volumeName + "]")
                return ''
            else:    
                code,reval = "23011", "Error when add a brick: " + message
    except Exception, e:
        code,reval = "23011", "Error when add a brick: " + str(e) 
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(volumeName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)                     

def migrateBrick(clusterName,volumeName):
    autoCommit = False
    try:
        data = web.input()
        serverName,code,reval = isPathExist(clusterName,volumeName,data)
        if code == 0:
            source = data.source
            target = data.target
            server_dir = target.split(':')
            target = Utils.getIPByName(server_dir[0].strip()) + ':' + server_dir[1]
            commandWithArgs = "gluster volume replace-brick " + volumeName + " " + source + " " + target + " start"
            status,message = Utils.executeOnServer(serverName,commandWithArgs)
            if status != 0:
                code,reval = "23012", "Error when migrate a brick:" + message
            else:
                description = "Brick Migration on volume ["+volumeName+"] from ["+source+"] to ["+target+"]"
                reference = volumeName+"#"+source+"#"+target
                operation_id = 2
                db.insert('task_info',description=description,reference=reference,operation_id=operation_id,cluster_name=clusterName)
                autoCommit_str = data.autoCommit
                if autoCommit_str is not None:
                    if autoCommit_str == 'true': 
                        autoCommit = True
                    else:
                        autoCommit = False
                        logger.info(description)
                        return ''                                                                                                           
    except Exception, e:
        if str(e) == "'autoCommit'":
            return ''    
        code,reval = "23012", "Error when migrate a brick:" + str(e) 
    if autoCommit:
        commandWithArgs ="gluster volume replace-brick " + volumeName + " " + source + " " + target + " "
        migrate_brick = Thread.MigrateBrickThread(2,commandWithArgs)
        migrate_brick.start()
        logger.info(commandWithArgs + ":autoCommit")
        return ''
    else:
        params = []
        params.append(clusterName)
        params.append(volumeName)
        result = Utils.errorCode(code, reval, params)
    logger.error(reval)
    raise web.HTTPError(status = "400 Bad Request", data = result)

'''
def removeBrick(clusterName,volumeName):
    try:
        data = web.data()
        serverName,code,reval = isPathExist(clusterName,volumeName,data)
        if code == 0:
            data_info = data.split('&')
            if len(data_info) == 1:
                bricks_info = data_info[0].split('=')
                bricks_data = web.storify({bricks_info[0]: bricks_info[1]}, _unicode=True)
                bricks = bricks_data.bricks
                bricks = bricks.replace(',',' ')
                commandWithArgs = "gluster --mode=script volume remove-brick " + volumeName + " " + bricks + " " + " force"
                status,message = Utils.executeOnServer(serverName,commandWithArgs)
                if status != 0:
                    code,reval = "23013","Error  where delete a brick" +message
                else:
                    return ''
            elif len(data_info) == 2:
                bricks_info = data_info[0].split('=')
                delete_info = data_info[1].split('=')
                bricks_data = web.storify({bricks_info[0]: bricks_info[1],delete_info[0]: delete_info[1]}, _unicode=True)
                bricks = bricks_data.bricks
                bricks_op = bricks.replace(',',' ')
                commandWithArgs = "gluster --mode=script volume remove-brick " + volumeName + " " + bricks_op + " " + " force"
                status,message = Utils.executeOnServer(serverName,commandWithArgs)
                if status != 0:
                    code,reval = "23013","Error  where delete a brick: " +message
                else:
                    if bricks_data.deleteData == 'true':
                        brick_split_info = bricks.split(',')
                        for brick_phsical_info in brick_split_info:
                            brick_phsical_info = brick_phsical_info.split(':')
                            brick_serverName =  brick_phsical_info[0]
                            brick_dir = brick_phsical_info[1]
                            commandWithArgs = "rm -rf " + brick_dir
                            status,message = Utils.executeOnServer(brick_serverName,commandWithArgs)
                            if status != 0:
                                code,reval = "23013","Error  where delete a brick: "+ message
                            else:
                                return ''
            else:
                code,reval = "30002","Input data is too long "                    
    except Exception, e:    
        code,reval = "23013","Error  where delete a brick: " + str(e)
    params = []
    params.append(clusterName)
    params.append(volumeName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)
'''

def removeBrick(clusterName,volumeName):
    try:
        data = web.input()
        serverName,code,reval = isPathExist(clusterName,volumeName,data)
        dataLen = len(data)
        if code == 0:
            if dataLen == 1:
                bricks = data.bricks
                bricks = bricks.replace(',',' ')
                commandWithArgs = "gluster --mode=script volume remove-brick " + volumeName + " " + bricks + " " + " force"
                status,message = Utils.executeOnServer(serverName,commandWithArgs)
                if status != 0:
                    code,reval = "23013","Error  where delete a brick" +message
                else:
                    return ''
            elif dataLen == 2:
                deleteData = data.deleteData
                bricksInfo = data.bricks
                bricks = bricksInfo.replace(',',' ')
                commandWithArgs = "gluster --mode=script volume remove-brick " + volumeName + " " + bricks + " " + " force"
                status,message = Utils.executeOnServer(serverName,commandWithArgs)
                if status != 0:
                    code,reval = "23013","Error  where delete a brick: " +message
                else:
                    if deleteData == 'true':
                        bricks = bricksInfo.split(',')
                        for brick in bricks:
                            brickSplit = brick.split(':')
                            brickServer =  brickSplit[0]
                            brickDir = brickSplit[1]
                            commandWithArgs = "rm -rf " + brickDir
                            status,message = Utils.executeOnServer(brickServer,commandWithArgs)
                            if status != 0:
                                code,reval = "23013","Error where delete a brick: "+ message
                                break
                        if status == 0:
                            return ''
                    else:
                        return ''
            elif dataLen == 3:
                deleteData = data.deleteData
                bricksInfo = data.bricks
                bricks = bricksInfo.replace(',',' ')
                commandWithArgs = "gluster --mode=script volume remove-brick " + volumeName + " " + bricks + " " + " force"
                status,message = Utils.executeOnServer(serverName,commandWithArgs)
                if status != 0:
                    code,reval = "23013","Error  where delete a brick: " +message
                else:
                    if deleteData == 'true':
                        bricks = bricksInfo.split(',')
                        for brick in bricks:
                            brickSplit = brick.split(':')
                            brickServer =  brickSplit[0]
                            brickDir = brickSplit[1]
                            commandWithArgs = "rm -rf " + brickDir
                            status,message = Utils.executeOnServer(brickServer,commandWithArgs)
                            if status != 0:
                                code,reval = "23013","Error where delete a brick: "+ message
                                break
                        if status == 0:
                            return ''
                    else:
                        return ''
            else:
                code,reval = "30002","Input data is too long "
    except Exception, e:
        code,reval = "23013","Error  where delete a brick: " + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(volumeName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def isVolumeExist(serverName,volumeName):
    commandWithArgs = "gluster volume info "+volumeName   
    status,message = Utils.executeOnServer(serverName,commandWithArgs)
    if status == 0:
        return True
    return False
              
def isPathExist(clusterName,volumeName,data):
    serverName = None
    code = None
    reval = None
    if len(data) == 0:
        code,reval = "30001", "Error missing input data" 
    else:
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code,reval = "20052", "Error cluster:"+clusterName+" not exist"
        else:
            cluster_id = cluster_id_info[0].id
            server_info = db.select('server_info',where='cluster_id=$cluster_id',what="name",vars=locals())
            if len(server_info) == 0:
                code,reval = "20053", "Error volume "+volumeName+" not exist in the cluster"
            else: 
                serverName = server_info[0].name
                if isVolumeExist(serverName,volumeName):
                    code,reval = 0,"SUCCESS"
                else:
                    code,reval = "20053", "Error volume "+volumeName+" not exist in the cluster"           
    return serverName,code,reval
    
