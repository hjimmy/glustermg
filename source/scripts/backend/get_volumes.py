import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
import paramiko

if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)

import Globals
import XmlHandler
from optparse import OptionParser
import commands

class Brick:
    name=""
    brickdir=""
    servername=""
    status=""
    freeSpace=0.0
    totalSpace=0.0

class Volume:
    default_replica_count = 2
    default_stripe_count = 4

    def __init__(self):
        self.name = ""
        self.volumeType = ""
        self.id = ""
        self.transportType = ""
        self.status = ""
        self.replicaCount = "0"
        self.stripeCount = "0"
        self.bricks = []
        self._id = ""
        self.totalSpace = 0.0
        self.freeSpace = 0.0
        self.smbSupport = False

def getvolumes(name=None):
    volume_list = []
    if name is None:
        volumeinfo = os.popen("gluster volume info").read()
    else:
        cmd = "gluster volume info %s" % name
        volumeinfo = os.popen(cmd).read()

    if volumeinfo.strip() != "":
        volume = None
        volstr = volumeinfo.split("\n")
        total = 0.0
        free = 0.0
        for vol in volstr:
            if vol.startswith("Volume Name"):
                volume = Volume()
                volume.name = vol.split(":")[1].strip()
                total = 0.0
                free = 0.0
            if vol.startswith("Type"):
                volume.volumeType = vol.split(":")[1].strip()
            if vol.startswith("Volume ID"):
                volume.id = vol.split(":")[1].strip()
            if vol.startswith("Status"):
                if vol.split(":")[1].strip().startswith("Started"):
                    volume.status = "ONLINE"
                else:
                    volume.status = "OFFLINE"
            if vol.startswith("Number Of Bricks"):
                if vol.index("x")!=-1:
                    if volume.volumeType.index("Stripe") != -1 or volume.volumeType.index("stripe") != -1:
                        vol.stripeCount = vol.split(":")[0].strip()
                elif volume.volumeType.index("Replica") != -1 or volume.volumeType.index("replica") != -1:
                        vol.replicaCount = vol.split(":")[0].strip()
                        vol.stripeCount = "0"
            if vol.startswith('Transport-type:'):
                volume.transportType = vol.split(":")[1].strip()
            if vol.startswith("Bricks"):
                continue
            if vol.startswith("Brick"):
                brick = Brick()
                brick.name = vol.split(":",1)[1].strip()
                brick.brickdir = brick.name.split(":")[1].strip()
                brick.servername = brick.name.split(":")[0].strip()
                cmd = 'python ' + Globals.BACKEND_SCRIPT + '/get_brick_status.py ' + volume.name + ' ' + brick.name
                status,output = executeOnServer(brick.servername, cmd)
                if status:
                    brick.status = 'OFFLINE'
		    xtot=0.0
		    xfree=0.0
		else:
		    list = output[:-1].split(' ')
                    brick.status = list[0]
                    xtot = float(list[1])
                    xfree = float(list[2])
                if xtot < 0.0:
                    xtot = 0.0
                if xfree < 0.0:
                    xfree = 0.0
                total += xtot
                free += xfree
                brick.freeSpace = xfree
                brick.totalSpace = xtot

                volume.bricks.append(brick)
#            if volume.volumeType != 'Distribute':
#                total = total / 2.0
#                free = free / 2.0
            if volume:
                volume.totalSpace = total
                volume.freeSpace = free
            if vol.strip() == '':
                if volume is not None:
                    if volume:
                        volume.totalSpace = total
                        volume.freeSpace = free
                        if volume.volumeType != 'Distribute':
                            volume.totalSpace = volume.totalSpace / 2
                            volume.freeSpace = volume.freeSpace / 2
                    volume_list.append(volume)
                    volume_list.append(volume)
                    volume=None
        return volume_list
    return None

def executeOnServer(serverName,commandWithArgs):
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
    except Exception,e:
        return -2,'Error when using pub key to connect remote host' + str(e)
    try:
#        key = paramiko.RSAKey.from_private_key_file('/opt/glustermg/keys/gluster.pem')
        key = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(serverName, 22, 'root', pkey=key)
               
        stdin,stdout,stderr = ssh.exec_command(commandWithArgs)
        res = stdout.read()
        ssh.close()
        strerr = stderr.read()
        if strerr is None or strerr.strip() is '':
            return 0,res
        return 1,strerr
    except Exception,e:
        return -1,"cannot connect "+ serverName + ' ' + str(e)

def getVolumeOptions(volumeName, option = None):
    cmd = 'gluster volume info ' + volumeName
    (status, output) = commands.getstatusoutput(cmd);
    if status != 0:
        return 'error while fetching information of volume:' + volumeName + '\n' + output
    optionprefix = 'Options Reconfigured'
    optionfound = False
    volumeinfo = output.split('\n')
    Dict = {}
    
    for info in volumeinfo:
        if info.startswith('Volume') == True or info.startswith('Type') == True or info.startswith('Status') == True or \
        info.startswith('Number') == True or info.startswith('Transport') == True or info.startswith('Brick') == True:
            continue
        if info.startswith(optionprefix) == True:
            optionfound = True
            continue 
        if optionfound == False:
            continue
        list = info.split(':')
        if len(list) !=2:
            optionfound = False
        Dict[list[0]] = list[1]
    return Dict

def getOptionDom(volumeName, option = None):
    options = getVolumeOptions(volumeName, option)
    responseDom = XmlHandler.ResponseXml()
    optionsTag = responseDom.appendTagRoute("options")
    
    for option in options.keys():
        optionTag = responseDom.createTag("option",None)
        optionsTag.appendChild(optionTag)
        optionTag.appendChild(responseDom.createTag("key",option))
        optionTag.appendChild(responseDom.createTag("value",options[option]))
        
    return optionsTag

def getVolumeDom(name=None):    
    volumes = getvolumes(name)
    if not volumes:
        return None
    responseDom = XmlHandler.ResponseXml()
    volumesTag = responseDom.appendTagRoute("volumes")
#  volumeTag = volumesTag.appendChild(responseDom.createTag("volume",""))
    for volume in volumes:
        volumeTag = responseDom.createTag("volume",None)
        volumesTag.appendChild(volumeTag)
        volumeTag.appendChild(responseDom.createTag("name",volume.name))
        volumeTag.appendChild(responseDom.createTag("status",volume.status))
        bricksTag = responseDom.createTag("bricks",None)
        volumeTag.appendChild(bricksTag)
        for brick in volume.bricks:
            bricktag = responseDom.createTag("brick",None)
            bricksTag.appendChild(bricktag)
            bricktag.appendChild(responseDom.createTag("qualifiedName",brick.name))
            bricktag.appendChild(responseDom.createTag("brickDirectory",brick.brickdir))
            bricktag.appendChild(responseDom.createTag("serverName",brick.servername))
            bricktag.appendChild(responseDom.createTag("status",brick.status.strip()))
            bricktag.appendChild(responseDom.createTag("freeSpace",brick.freeSpace))
            bricktag.appendChild(responseDom.createTag("totalSpace",brick.totalSpace))
#    volumeTag.appendChild(responseDom.createTag("cifsShared",""))
        nasTag = responseDom.createTag("nasProtocols",None)
        volumeTag.appendChild(nasTag)
        nasTag.appendChild(responseDom.createTag("nasProtocol",'GLUSTERFS'))
    
        optionsTag = getOptionDom(volume.name, option = None)
        volumeTag.appendChild(optionsTag)
        volumeTag.appendChild(responseDom.createTag("stripeCount",volume.stripeCount))
        volumeTag.appendChild(responseDom.createTag("replicaCount",volume.replicaCount))
        if volume.transportType.lower() == 'tcp':
            transportType = 'ETHERNET'
        else:
            transportType = 'INFINIBAND'
        volumeTag.appendChild(responseDom.createTag("transportType",transportType))
#    volumeTag.appendChild(responseDom.createTag("volumeCifsUsers",None))
        volumeTag.appendChild(responseDom.createTag("volumeType",volume.volumeType))
        volumeTag.appendChild(responseDom.createTag("totalSpace",volume.totalSpace))
        volumeTag.appendChild(responseDom.createTag("freeSpace",volume.freeSpace))
        if name is not None:
            return volumeTag
    return volumesTag

def main():
    name = None
    if len(sys.argv) ==2 or len(sys.argv) > 2:
        name = sys.argv[1]
    responseXml = getVolumeDom(name)
    if responseXml:
        print responseXml.toxml(),'\n'
    sys.exit(0)

if __name__ == "__main__":
    main()
