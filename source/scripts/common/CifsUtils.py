import re
import os
import sys
import Utils
import Globals

def isVolumeInCifs(path):
    exist = os.path.exists(path)
    return str(exist)

def fetchVolumeCifsUsers(VolumeDom):
    
    volumeElement = VolumeDom.getElementsByTagName("volume")
    for volume in volumeElement:
        nameTag = volume.getElementsByTagName("name")
        volumeName = nameTag[0].childNodes[0].data

        ##check whethe the volume supports samba
        volume.appendChild(VolumeDom.createTag('smbSupport',isVolumeInCifs('/cifs/' + volumeName).lower()))
        ID = Globals.db.select('volume_info',what='*',where='name=$volumeName',vars=locals())
        if len(ID) == 0:
           id='1000'
        else:
           id = str(ID[0].id)
        volume.appendChild(VolumeDom.createTag('intid', id))
        lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
        linenum = 0
        volume_exist = False
        value = {}
        value["shared"] = "no"
        value["owner"] = ""

        for line in lines:
            m = re.match("\["+volumeName+"\]",line)
            if m is not None:
                token = lines[linenum + 1].strip().split("=")
                value[token[0].strip()] = token[1].strip()
                volume_exist = True
                break
            linenum = linenum + 1

        if volume_exist == True:
            volume.appendChild(VolumeDom.createTag("enableCifs","true"))
            isshared = 'false'
            if value["shared"].lower() == 'yes':
                isshared = 'true'
            volume.appendChild(VolumeDom.createTag("isShared", isshared))
            volume.appendChild(VolumeDom.createTag("owner",value["owner"]))
            nasProtocolsTag = volume.getElementsByTagName("nasProtocols")
            nasProtocolsTag[0].appendChild(VolumeDom.createTag("nasProtocol", "CIFS"))
        else:
            volume.appendChild(VolumeDom.createTag("enableCifs","false"))

def createVolumeCIFSUsers(volumeName, isShared, owner, hostAllowed):
    if isShared == "true":
        command = "%s/create_volume_cifs_shared.py %s %s" % (Globals.BACKEND_SCRIPT, volumeName, hostAllowed)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            return False
        if not addVolumeCifsConf(volumeName, isShared, owner):
            sys.stderr.write("Failed to add volume %s in volume cifs configuration\n" % (volumeName))
            return False
        return True
    else:
        command = "%s/create_volume_cifs.py %s %s %s" % (Globals.BACKEND_SCRIPT, volumeName, owner, hostAllowed)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            return False
        if not addVolumeCifsConf(volumeName, isShared, owner):
            sys.stderr.write("Failed to add volume %s in volume cifs configuration\n" % (volumeName))
            return False
        return True

def updateVolumeCIFSUsers(volumeName, isShared, owner, hostAllowed):
    if isShared == "true":
        command = "%s/update_volume_cifs_shared.py %s %s" % (Globals.BACKEND_SCRIPT, volumeName, hostAllowed)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            return False
        if not updateVolumeCifsConf(volumeName, isShared, owner):
            sys.stderr.write("Failed to update volume %s in volume cifs configuration\n" % (volumeName))
            return False
        return True
    else:
        command = "%s/update_volume_cifs.py %s %s %s" % (Globals.BACKEND_SCRIPT, volumeName, owner, hostAllowed)
        status = Utils.runCommand(command, output=True, root=True, shell=True)
        if status["Status"] != 0:
            return False
        if not updateVolumeCifsConf(volumeName, isShared, owner):
            sys.stderr.write("Failed to update volume %s in volume cifs configuration\n" % (volumeName))
            return False
        return True

def addVolumeCifsConf(volumeName, isShared, owner):
    lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
    try:
        fp = open(Globals.CIFS_VOLUME_FILE, "w")
        for line in lines:
            if not line.strip():
                continue
            if line.strip().split(":")[0] != volumeName:
                fp.write("%s" % line)
        fp.write("[%s]\n" % volumeName)
        if isShared == "true":
            fp.write("  shared = yes\n")
        else:
            fp.write("  owner = %s\n" % owner)
        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_VOLUME_FILE, str(e)))
        return False
    return True

def updateVolumeCifsConf(volumeName, isShared, owner):
    lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
    exists = 0
    try:
        fp = open(Globals.CIFS_VOLUME_FILE, "r")
####  get the start_line  junli.li
        for line in lines:
            if not line.strip():
                continue
            if line.strip() == "["+volumeName+"]":
                start_line = lines.index(line)
                exists = 1
                break
####  whether the volume exists?  junli.li
        if exists == 0:
            sys.stderr.write("%s volume does not exist\n" % (volumeName))
            sys.exit(10)
        fp.close()

        fp = open(Globals.CIFS_VOLUME_FILE, "w")
        lineNo = 0
        for eachline in lines:
            if lineNo < start_line:
                fp.write(eachline)
            elif lineNo > start_line + 1:
                fp.write(eachline)
            lineNo = lineNo + 1

        fp.write("[%s]\n" % (volumeName))
        if isShared == "true":
            fp.write("  shared = yes\n")
        else:
            fp.write("  owner = %s\n" % owner)
        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_VOLUME_FILE, str(e)))
        return False
    return True

def startCifsReExport(volumeName, serverName):
    command = "%s/start_volume_cifs.py %s %s" % (Globals.BACKEND_SCRIPT, volumeName, serverName)
    status = Utils.runCommand(command, output=True, root=True, shell=True)
    if status["Status"] == 0:
        return True
    else:
        sys.stderr.write("Failed to start cifs reexport:[ %s ] \n" % (volumeName))
        return False
    
def stopCifsReExport(volumeName):
    command = "%s/stop_volume_cifs.py %s" % (Globals.BACKEND_SCRIPT, volumeName)
    status = Utils.runCommand(command, output=True, root=True, shell=True)
    if status["Status"] == 0:
        return True
    else:
        sys.stderr.write("Failed to stop cifs reexport:[ %s ] \n" % (volumeName))
        return False
    
def deleteVolumeCIFSUser(volumeName):    
    command = "%s/delete_volume_cifs.py %s" % (Globals.BACKEND_SCRIPT, volumeName)
    status = Utils.runCommand(command, output=True, root=True, shell=True)
    if status["Status"] != 0:
        return False
    if not removeVolumeCifsConf(volumeName):
        sys.stderr.write("Failed to remove volume %s in volume cifs configuration\n" % (volumeName))
        return False
    return True
    
def removeVolumeCifsConf(volumeName):
    lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
    exists = 0
    try:
        fp = open(Globals.CIFS_VOLUME_FILE, "r")
        for line in lines:
            if not line.strip():
                continue
            if line.strip() == "["+volumeName+"]":
                start_line = lines.index(line)
                exists = 1
                break
####  whether the volume exists?  
        if exists == 0:
            sys.stderr.write("%s volume does not exist\n" % (volumeName))
            sys.exit(10)
        fp.close()
###   modify the Globals.CIFS_VOLUME_FILE file. 
###   delete the lines between start_line and start_line+1
        fp = open(Globals.CIFS_VOLUME_FILE, "w")
        lineNo = 0
        for eachline in lines:
            if lineNo < start_line:
                fp.write(eachline)
            elif lineNo > start_line + 1:
                fp.write(eachline)
            lineNo = lineNo + 1
        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_VOLUME_FILE, str(e)))
        return False
    return True
