import threading
import Globals
import Utils
from time import sleep
from services import taskService
from services import volumeService
import xml.etree.ElementTree
from decimal import *
from XmlHandler import *
from CifsUtils import *

class ServerDetailsThread(threading.Thread):    
    def __init__(self,interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):  
        while not self.thread_stop:
            server_info = Globals.db.select('server_info')
            for server in server_info:
                serverName = str(server.name)
                cmd = 'python ' + Globals.BACKEND_SCRIPT + 'get_server_details.py 2>/dev/null'
                status,message = Utils.executeOnServer(serverName, cmd)
                if status == 0:
		    serverName = serverName.strip()
                    Globals.mc.set(serverName+'_server',message)
		else:
                    Globals.mc.delete(serverName+'_server',1)
            sleep(self.interval)
    def stop(self):
        self.thread_stop = True

class VolumeInfoThread(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
           cluster_info = Globals.db.select('cluster_info')
           if len(cluster_info) != 0:
               server = None
               for cluster in cluster_info:
                   clusterid = cluster.id
                   clusterName = cluster.name
                   server_info = Globals.db.select('server_info', where='cluster_id=$clusterid', vars=locals())
                   if len(server_info) != 0:
		       server = None
                       for server in server_info:
                           if Utils.isOnline(str(server.name)) == True:
                               break
                       if server is not None:
                           volumes = Globals.db.select('volume_info', where='cluster_id=$clusterid', vars=locals())
                           if len(volumes) != 0:
                               for v in volumes:
#                         volumeInfo = volumeService.getVolume(clusterName, str(v.name).strip(),False)
                                   cmd = "python " + Globals.BACKEND_SCRIPT + "get_volumes.py " + str(v.name).strip()
                                   status, output = Utils.executeOnServer(str(server.name), cmd)
                                   if status:
                                       Globals.mc.delete(str(v.name)+'_volume',1)
                                       continue
                                   dom = ResponseXml()
                                   dom.parseString(output)
                                   fetchVolumeCifsUsers(dom)
                                   Globals.mc.set(str(v.name)+'_volume', dom.toxml())
           sleep(self.interval)

    def stop(self):
        self.thread_stop = True
class MigrateBrickThread(threading.Thread):
    def __init__(self,interval,operation):
        threading.Thread.__init__(self)
        self.interval = interval
        self.operation = operation
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            status,local_IP = Utils.getLocal_IP()
            localIP =  local_IP.strip()
            commandWithArgs = self.operation + "status"
            status,message = Utils.executeOnServer(localIP,commandWithArgs)
            code,message = taskService.getMigrateStatus(message)
            if code == "6":
                commandWithArgs = self.operation + "commit"
                status,message = Utils.executeOnServer(localIP, commandWithArgs)
                self.thread_stop = True
            sleep(self.interval)
    def stop(self):
        self.thread_stop = True

class ClusterDetailsThread(threading.Thread):
    def __init__(self,interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            cluster_info = Globals.db.select('cluster_info')
            if len(cluster_info) != 0:
                for cluster in cluster_info:
                    serversInfo = []
                    sum = 0
                    online = 0
                    servers = []
                    totalSpace = Decimal("0.0")
                    usedSpace = Decimal("0.0")
                    cluster_id = cluster.id
                    server_info = Globals.db.select('server_info',where='cluster_id=$cluster_id' ,what="name",vars=locals())
                    if len(server_info) != 0:
                        sum = len(server_info)
                        for server in server_info:
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
                    strs =  str(cluster.name) + "_servers"
                    Globals.mc.set(strs,serversInfo)
            sleep(self.interval)
    def stop(self):
        self.thread_stop = True

class TaskDetailsThread(threading.Thread):
    def __init__(self,interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            tasks_sum = 0
            tasks_commit = 0
            serversInfo = []
            totalSpace = Decimal("0.0")
            usedSpace = Decimal("0.0")
            cluster_info = Globals.db.select('cluster_info')
            if len(cluster_info) != 0:
                for cluster in cluster_info:
                    clusterName = cluster.name
                    task_info = Globals.db.select('task_info ,operation_info',where='task_info.operation_id=operation_info.id and task_info.cluster_name=$clusterName ',what = "task_info.id as taskID,description,reference,operation_id,operation_info.id,operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported",vars=locals())
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
                        strs =  str(clusterName) + "_tasks"
                        tasksInfo = tasks_commit,tasks_sum
                        Globals.mc.set(strs,tasksInfo)
            sleep(self.interval)
    def stop(self):
        self.thread_stop = True

class VolumeDetailsThread(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            cluster_info = Globals.db.select('cluster_info',what='*')
            if len(cluster_info) != 0:
		onlineNum = 0
                totalNum = 0
		volumes = []
                for cluster in cluster_info:
                    clusterid = cluster.id
                    clusterName = cluster.name
                    server_info = Globals.db.select('server_info', where='cluster_id=$clusterid',vars=locals())
                    if len(server_info) != 0:
                        for server in server_info:
                            if Utils.isOnline(str(server.name)) == False:
                                continue
 
                        status, message = Utils.executeOnServer(str(server.name), 'gluster volume list')
                        if  message.strip() != 'No volumes present in cluster':
		            volumeList = message.split('\n')
                            onlineNum = 0
                            totalNum = 0
                            volumes = []
                            for v in volumeList:
                                message = Globals.mc.get(str(v).strip()+"_volume")
                                if message is None:
                                    if v.strip() != '':
                                        cmd = "python " + Globals.BACKEND_SCRIPT + "get_volumes.py " + v
                                        status,message = Utils.executeOnServer(str(server.name), cmd)
                                        totalNum += 1
                                        volumes.append(v)
                                    if status != 0:
                                        continue
                                if message is not None:
                                    weblog = xml.etree.ElementTree.fromstring(message)
                                    for entry in weblog.findall('status'):
                                        status = entry.text
                                    if status.strip().lower() == 'online':
                                        onlineNum += 1
		    clusterVolumeInfo = []
                    clusterVolumeInfo.append(totalNum)
                    clusterVolumeInfo.append(onlineNum)
                    clusterVolumeInfo.append(volumes)
                    key = str(clusterName) + '_volumes'
                    Globals.mc.set(key,clusterVolumeInfo)
            sleep(self.interval)

    def stop(self):
        self.thread_stop = True
