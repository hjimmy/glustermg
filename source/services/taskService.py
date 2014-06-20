###added by jian.hou task operations
import web
import os
import logging
import logging.config
import commands
import re
from scripts.common import XmlHandler, Globals, Utils

db =Globals.db
STATUS_CODE_SUCCESS = "0"
STATUS_CODE_FAILURE = "1"
STATUS_CODE_PART_SUCCESS = "2"
STATUS_CODE_RUNNING = "3"
STATUS_CODE_PAUSE = "4"
STATUS_CODE_WARNING = "5"
STATUS_CODE_COMMIT_PENDING = "6"
STATUS_CODE_ERROR = "7"

logging.config.fileConfig(Globals.LOG_CONF)
logger = logging.getLogger("Task")
'''
logger.debug("debug message")
logger.info("info message")
logger.warn("warn message")
logger.error("error message")
logger.critical("critical message")
'''

def getTasks(clusterName):
    try:
        show_len = 100
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20052", "Error cluster: "+clusterName+" not exist"
        else:
            task_info = db.select('task_info ,operation_info',where='task_info.operation_id=operation_info.id and task_info.cluster_name=$clusterName',what = "task_info.id as taskID,description,reference,operation_id,operation_info.id,operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported",vars=locals())
            tasksTag = createTasksTag()
            task_len = len(task_info)
            if task_len == 0:
                logger.info("There is no task info")
                return tasksTag.toxml()
	    elif task_len > show_len:
                task_start = task_len - show_len
                task_info = db.select('task_info ,operation_info',where='task_info.operation_id=operation_info.id and task_info.cluster_name=$clusterName limit $task_start,$task_len ',what = "task_info.id as taskID,description,reference,operation_id,operation_info.id,operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported",vars=locals())
            for task in task_info:
                if task.operation_id == 2:
                    migrate = Migrate_operation()
                    (code, reval) = migrate.get_migrate_info(task.reference)
                    (code,message) = getMigrateStatus(reval)
                    percentCompleted = percentCompleted = '0.0'
                elif task.operation_id == 1:
                    disk = Disk_operation()
                    (code, reval) = disk.get_disk_info(task.reference)
                    messages = reval.split('\n')
                    message = messages[len(messages) - 1].strip()[:-1]
                    code, message = getInitialStatus(reval)
                    percentCompleted = '0.0'
                else:
                    rebal = Rebalance_operation()
                    (code, reval) = rebal.get_rebalance_info(task.reference)
                    messages = reval.split('\n')
                    message = messages[len(messages) - 1].strip()
                    code, message = getRebalanceStatus(reval)
                    percentCompleted  = '0.0'
                task_info_xml = addTaskTag(tasksTag,task.taskID,task.commitSupported,task.description,task.taskID,task.pauseSupported,task.reference,code,message,percentCompleted,task.percentageSupported,task.stopSupported,task.operation_type)
            logger.info("Get all tasks info")
            return task_info_xml
    except Exception,e:
        code, reval = "24001", "Error when get all tasks info:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def getTask(clusterName,taskID):
    try:
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20052", "Error  cluster: "+clusterName+" not exist"
        else:
            task_info = db.select('task_info,operation_info',where='task_info.operation_id=operation_info.id and task_info.id=$taskID and task_info.cluster_name=$clusterName',what = "*",vars=locals())
            if len(task_info) == 0:
                code, reval = "20056", "Error the task not exist"
            else:
                task =task_info[0]
                if task.operation_id == 2:
                    task_info=task.reference.replace('#',' ')
                    migrate = Migrate_operation()
                    (status, output) = migrate.get_migrate_info(task.reference)
                    (code,message) = getMigrateStatus(output)
                    percentCompleted = percentCompleted = '0.0'
                elif task.operation_id == 1:
                    disk = Disk_operation()
                    (status, output) = disk.get_disk_info(task.reference)
                    messages = output.split('\n')
                    message = messages[len(messages) - 1].strip()[:-1]
                    code, message = getInitialStatus(output)
                    percentCompleted = '0.0'
                else:
                    rebal = Rebalance_operation()
                    (status, output) = rebal.get_rebalance_info(task.reference)
                    messages = output.split('\n')
                    message = messages[len(messages) - 1].strip()
                    code, message = getRebalanceStatus(output)
                    percentCompleted  = '0.0'
                task_info_xml = taskTag(taskID,task.commitSupported,task.description,taskID,task.pauseSupported,task.reference,code,message,percentCompleted,task.percentageSupported,task.stopSupported,task.operation_type)
                logger.info("Get task info")
                return task_info_xml
    except Exception,e:
        code, reval = "24001", "Error when get task info:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(taskID)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def managerTask(clusterName,taskID):
    try:
        data = web.input()
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20052", "Error cluster:"+clusterName+" not exist"
        else:
            task_info = db.select('task_info,operation_info',where='task_info.operation_id=operation_info.id and task_info.id=$taskID and task_info.cluster_name=$clusterName',what = "*",vars=locals())
            if len(task_info) == 0:
                code, reval = "20056", "Error the task not exist"
            else:
                task =task_info[0]
                if data.operation == 'stop':
                    if task.operation_id == 2:
                        migrate = Migrate_operation()
                        (code, reval) = migrate.stop_migrate(task.reference)
                        if code == 0:
                            return reval
                    elif task.operation_id == 1:
                        disk = Disk_operation()
                        (code, reval) = disk.stop_disk(task.reference)
                        if code == 0:
                            return reval
                    else:
                        rebal = Rebalance_operation()
                        (code, reval) = rebal.stop_rebalance(task.reference)
                        if code == 0:
                            return reval
                if data.operation == 'pause':
                    if task.operation_id == 2:
                        task_info=task.reference.replace('#',' ')
                        migrate = Migrate_operation()
                        (code, reval) = migrate.pause_migrate(task.reference)
                        if code == 0:
                            return reval
                    elif task.operation_id == 1:
                        disk = Disk_operation()
                        (code,reval) = disk.pause_disk(task.reference)
                        if code == 0:
                            return reval
                    else:
                        rebal = Rebalance_operation()
                        (code, reval) = rebal.pause_rebalance(task.reference)
                        if code == 0:
                            return reval
                if data.operation == 'resume':
                    if task.operation_id == 2:
                        task_info=task.reference.replace('#',' ')
                        migrate = Migrate_operation()
                        (code, reval) = migrate.resume_migrate(task.reference)
                        if code == 0:
                            return reval
                    elif task.operation_id == 1:
                        disk = Disk_operation()
                        (code, reval) = disk.resume_disk(task.reference)
                        if code == 0:
                            return reval
                    else:
                        rebal = Rebalance_operation()
                        (code, reval) = rebal.resume_rebalance(task.reference)
                        if code == 0:
                            return reval
                if data.operation == 'commit':
                    if task.operation_id == 2:
                        task_info=task.reference.replace('#',' ')
                        migrate = Migrate_operation()
                        (code, reval) = migrate.commit_migrate(task.reference)
                        if code == 0:
                            return reval
                    elif task.operation_id == 1:
                        disk = Disk_operation()
                        (code, reval) = disk.commit_disk(task.reference)
                        if code == 0:
                            return reval
                    else:
                        rebal = Rebalance_operation()
                        (code, reval) = rebal.commit_rebalance(task.reference)
                        if code == 0:
                            return reval
                else:
                    code, reval = "24004", "Error Invalid Task Operation"
    except Exception,e:
        code, reval = "24003", "Error when  manager a task:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    params.append(taskID)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def deleteTask(clusterName,taskID):
    try:
        cluster_id_info = db.select('cluster_info',where='name=$clusterName',what="id",vars=locals())
        if len(cluster_id_info) == 0:
            code, reval = "20052", "Error cluster: "+clusterName+" not exist"
        else:
            task_info = db.select('task_info,operation_info',where='task_info.operation_id=operation_info.id and task_info.id=$taskID and task_info.cluster_name=$clusterName',what = "*",vars=locals())
            if len(task_info) == 0:
                code, reval = "20056", "Error the task not exist"
            else:
                is_task_delete = db.delete('task_info',where='id=$taskID',vars=locals())
                if is_task_delete == 0:
                    code, reval = "24005","Error when  delete a task"
                else:
                    return ''
    except Exception,e:
        code, reval = "24005", "Error when  delete a task:" + str(e)
    logger.error(reval)
    params = []
    params.append(clusterName)
    result = Utils.errorCode(code, reval, params)
    raise web.HTTPError(status = "400 Bad Request", data = result)

def addTaskTag(tasksTag,name,commitSupported,description,id,pauseSupported,reference,code,message,percentCompleted,percentageSupported,stopSupported,type):
        responseDom = XmlHandler.ResponseXml()
        taskTag  = responseDom.appendTagRoute("task")
        taskTag.appendChild(responseDom.createTag("name", name))
        taskTag.appendChild(responseDom.createTag("commitSupported", commitSupported))
        taskTag.appendChild(responseDom.createTag("description", description))
        taskTag.appendChild(responseDom.createTag("id", id))
        taskTag.appendChild(responseDom.createTag("reference", reference))

        statusTag  = responseDom.appendTagRoute("status")
        statusTag.appendChild(responseDom.createTag("code", code))
        statusTag.appendChild(responseDom.createTag("message", message))
        statusTag.appendChild(responseDom.createTag("percentCompleted", percentCompleted))
        statusTag.appendChild(responseDom.createTag("percentageSupported", percentCompleted))
        taskTag.appendChild(statusTag)
        taskTag.appendChild(responseDom.createTag("stopSupported", stopSupported))
        taskTag.appendChild(responseDom.createTag("type", type))
        tasksTag.appendChild(taskTag)
        return tasksTag.toxml()

def taskTag(name,commitSupported,description,id,pauseSupported,reference,code,message,percentCompleted,percentageSupported,stopSupported,type):
        responseDom = XmlHandler.ResponseXml()
        taskTag  = responseDom.appendTagRoute("task")
        taskTag.appendChild(responseDom.createTag("name", name))
        taskTag.appendChild(responseDom.createTag("commitSupported", commitSupported))
        taskTag.appendChild(responseDom.createTag("description", description))
        taskTag.appendChild(responseDom.createTag("id", id))
        taskTag.appendChild(responseDom.createTag("reference", reference))

        statusTag  = responseDom.appendTagRoute("status")
        statusTag.appendChild(responseDom.createTag("code", code))
        statusTag.appendChild(responseDom.createTag("message", message))
        statusTag.appendChild(responseDom.createTag("percentCompleted", percentCompleted))
        statusTag.appendChild(responseDom.createTag("percentageSupported", percentCompleted))
        taskTag.appendChild(statusTag)
        taskTag.appendChild(responseDom.createTag("stopSupported", stopSupported))
        taskTag.appendChild(responseDom.createTag("type", type))
        return taskTag.toxml()

def createTasksTag():
        responseDom = XmlHandler.ResponseXml()
        tasksTag = responseDom.appendTagRoute("tasks")
        return tasksTag

def getRebalanceStatus(output):
    if re.match('^rebalance completed.*', output) != -1:
        code = STATUS_CODE_SUCCESS
        message = 'rebalance completed'
    elif re.match('.*in progress.*', output) != -1:
        code = STATUS_CODE_RUNNING
        message = 'rebalance is running'
    else:
        code = STATUS_CODE_FAILURE
        message = 'rebalance failed'
    logger.info(message)
    return code,message

def getInitialStatus(output):
    if re.match('STATUS_CODE_SUCCESS', output):
        code = STATUS_CODE_SUCCESS
        message = 'initialize disk successfully'
    elif re.match('STATUS_CODE_RUNNING', output):
        code = STATUS_CODE_RUNNING
        message = 'initializing disk is running'
    elif re.match('STATUS_CODE_FAILURE', output):
        code = STATUS_CODE_FAILURE
        message = 'initialize disk failed'
    else:
        code = STATUS_CODE_FAILURE
        message = 'initialize disk failed'
    logger.info(message)
    return code,message

def getMigrateStatus(message):
    if re.match("^Number of files migrated.*Migration complete $",message) or re.match("^Number of files migrated = 0 .*Current file=",message):
        code = STATUS_CODE_COMMIT_PENDING
        return code,message
    elif re.match("^Number of files migrated.*Current file=.*",message):
        code = STATUS_CODE_RUNNING
        return code,"Brick Migration Started."
    elif re.match("^replace brick has been paused.*",message) :
        code = STATUS_CODE_PAUSE
        return code,"Brick Migration Paused",message
    elif re.match("replace-brick not started on volume*",message):
        code = STATUS_CODE_SUCCESS
        return code,"Brick Migration Committed."
    else:
        code = STATUS_CODE_FAILURE
        return code,message

class Disk_operation:
    def get_disk_info(self, reference):
        server_disk = reference.split(':')
        chkcmd = 'python '+ Globals.BACKEND_SCRIPT + '/get_format_device_status.py ' + server_disk[1]
        hostName = os.popen('hostname').read()
        if Utils.isLocalHost(server_disk[1].strip()):
            (status, output) = commands.getstatusoutput(chkcmd)
        else:
            (status, output) = Utils.executeOnServer(server_disk[0].strip(), chkcmd)
        return status,output

    def stop_disk(self, reference):
        return ('24004','Error: Stop/Pause/Resume/Commit is not supported in Disk Initialization')
    def pause_disk(self, clusterName, reference):
        return ('24004','Error: Stop/Pause/Resume/Commit is not supported in Disk Initialization')
    def resume_disk(self, clusterName, reference):
        return ('24004','Error: Stop/Pause/Resume/Commit is not supported in Disk Initialization')
    def commit_disk(self, clusterName, reference):
        return ('24004','Error: Stop/Pause/Resume/Commit is not supported in Disk Initialization')

class Rebalance_operation:
    def get_rebalance_info(self,reference):
        chkcmd = 'gluster volume rebalance ' + reference + ' status'
        (status, output) = commands.getstatusoutput(chkcmd)
        return status,output
    def stop_rebalance(self, clusterName, reference):
        chkcmd = 'gluster volume rebalance ' + reference + ' stop'
        (status, output) = commands.getstatusoutput(chkcmd)
        if status == 0:
            return 0,""
        return (status, output)
    def pause_rebalance(self,reference):
        return ('24004','Pause/Resume/Commit is not supported in Volume Rebalance')
    def resume_rebalance(self, clusterName, reference):
        return ('24004','Pause/Resume/Commit is not supported in Volume Rebalance')
    def commit_rebalance(self, clusterName, reference):
        return ('24004','Pause/Resume/Commit is not supported in Volume Rebalance')

class Migrate_operation:
    def get_migrate_info(self,taskReference):
        reference = taskReference.replace('#',' ')
        chkcmd = 'gluster volume replace-brick ' + reference + ' status'
        (status, output) = commands.getstatusoutput(chkcmd)
        return status, output
    def stop_migrate(self,taskReference):
        reference = taskReference.replace('#',' ')
        chkcmd = 'gluster volume replace-brick ' + reference + ' abort'
        (status, output) = commands.getstatusoutput(chkcmd)
        if status == 0:
            return 0,""
        return (status, output)

    def pause_migrate(self,taskReference):
        reference = taskReference.replace('#',' ')
        chkcmd = 'gluster volume replace-brick ' + reference + ' pause'
        (status, output) = commands.getstatusoutput(chkcmd)
        if status == 0:
            return 0,""
        return (status, output)

    def resume_migrate(self,taskReference):
        reference = taskReference.replace('#',' ')
        chkcmd = 'gluster volume replace-brick ' + reference + ' start'
        (status, output) = commands.getstatusoutput(chkcmd)
        if status == 0:
            return 0,""
        return (status, output)

    def commit_migrate(self,taskReference):
        reference = taskReference.replace('#',' ')
        chkcmd = 'gluster volume replace-brick ' + reference + ' commit force'
        (status, output) = commands.getstatusoutput(chkcmd)
        if status == 0:
            return 0,""
        return (status, output)
