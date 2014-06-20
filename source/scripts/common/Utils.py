#  Copyright (C) 2011 Gluster, Inc. <http://www.gluster.com>
#  This file is part of Gluster Management Gateway (GlusterMG).
#
#  GlusterMG is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published
#  by the Free Software Foundation; either version 3 of the License,
#  or (at your option) any later version.
#
#  GlusterMG is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see
#  <http://www.gnu.org/licenses/>.
#

import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
import re
import syslog
import subprocess
import time
import tempfile
import glob
import commands
import paramiko

import Globals
import XmlHandler

RUN_COMMAND_ERROR = -1024
LOG_SYSLOG = 1
SYSLOG_REQUIRED = False
LOG_FILE_NAME = None
LOG_FILE_OBJ = None
logOpened = False
sshCommandPrefix = "ssh -l root -q -i /opt/glustermg/keys/gluster.pem -o BatchMode=yes -o GSSAPIAuthentication=no -o PasswordAuthentication=no -o StrictHostKeyChecking=no".split()
sshCommandPrefixShell = "ssh -l root -q -i /opt/glustermg/keys/gluster.pem -o BatchMode=yes -o GSSAPIAuthentication=no -o PasswordAuthentication=no -o StrictHostKeyChecking=no"
try:
    commandPath = "/opt/glustermg/%s/backend" % os.environ['GMG_VERSION']
except KeyError, e:
    commandPath = "/opt/glustermg/2.4/backend"

def log(priority, message=None):
    global logOpened
    if not logOpened:
        syslog.openlog(os.path.basename(sys.argv[0]))
        logOpened = True

    if type(priority) == type(""):
        logPriority = syslog.LOG_INFO
        logMessage = priority
    else:
        logPriority = priority
        logMessage = message
    if not logMessage:
        return
    #if Globals.DEBUG:
    #    sys.stderr.write(logMessage)
    else:
        syslog.syslog(logPriority, logMessage)
    return


def isString(value):
    return (type(value) == type("") or type(value) == type(u""))


def getTempFileName():
    filedesc, filename = tempfile.mkstemp(prefix="GSP_")
    os.close(filedesc)
    return filename


def readFile(fileName, lines=False):
    content = None
    try:
        fp = open(fileName)
        if lines:
            content = fp.readlines()
        else:
	    content = fp.read()
        fp.close()
        return content
    except IOError, e:
        log("failed to read file %s: %s" % (fileName, str(e)))
    if lines:
        return []
    else:
        return ""


def writeFile(fileName, content):
    try:
        fp = open(fileName, "w")
        if isString(content):
            fp.write(content)
        elif type(content) == type([]):
            fp.writelines(content)
        fp.close()
        return True
    except IOError, e:
        log("failed to write file %s: %s" % (fileName, str(e)))
    return False


def removeFile(fileName, root=False):
    if not os.path.exists(fileName):
	return True
    if root:
        if runCommand("rm %s" % fileName, root=True) == 0:
            return True
        return False
    try:
        os.remove(fileName)
        return True
    except OSError, e:
        log("Failed to remove file %s: %s" % (fileName, str(e)))
    return False


def runCommandBG(command, stdinFileObj=None, stdoutFileObj=None, stderrFileObj=None,
                 shell=False, root=None):
    if shell:
        if not isString(command):
            return None
    else:
        if isString(command):
            command = command.split()

    if root == True:
        if shell:
            command = "sudo " + command
        else:
            command = ['sudo'] + command
    elif isString(root):
        if shell:
            command = "sudo -u " + root + " " + command
        else:
            command = ['sudo', '-u', root] + command

    if not stdinFileObj:
        stdinFileObj=subprocess.PIPE
    if not stdoutFileObj:
        stdoutFileObj=subprocess.PIPE
    if not stderrFileObj:
        stderrFileObj=subprocess.PIPE

    try:
        process = subprocess.Popen(command,
                                   bufsize=-1,
                                   stdin=stdinFileObj,
                                   stdout=stdoutFileObj,
                                   stderr=stderrFileObj,
                                   shell=shell)
        return process
    except OSError, e:
        log("runCommandBG(): Failed to run command [%s]: %s" % (command, e))
    return None


def runCommand(command,
               input='', output=False,
               shell=False, root=None):
    rv = {}
    rv["Status"] = RUN_COMMAND_ERROR
    rv["Stdout"] = None
    rv["Stderr"] = None

    try:
        stdinFileName = getTempFileName()
        stdinFileObj = open(stdinFileName, "w")
        stdinFileObj.write(input)
        stdinFileObj.close()
        stdinFileObj = open(stdinFileName, "r")

        stdoutFileName = getTempFileName()
        stdoutFileObj = open(stdoutFileName, "w")

        stderrFileName = getTempFileName()
        stderrFileObj = open(stderrFileName, "w")
    except IOError, e:
        log("Failed to create temporary file for executing command [%s]: %s" % (command, e))
        if output:
            return rv
        return rv["Status"]

    stdoutContent = None
    stderrContent = None

    process = runCommandBG(command,
                           stdinFileObj=stdinFileObj,
                           stdoutFileObj=stdoutFileObj,
                           stderrFileObj=stderrFileObj,
                           shell=shell, root=root)
    if process:
        rv['Status'] = process.wait()
        rv['Stdout'] = readFile(stdoutFileName)
        rv['Stderr'] = readFile(stderrFileName)

    os.remove(stdinFileName)
    os.remove(stdoutFileName)
    os.remove(stderrFileName)

    if output:
        return rv
    return rv["Status"]


def daemonize():
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e:
        #sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        return False
	
    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 
	
    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent
            sys.exit(0) 
    except OSError, e: 
        #sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        return False 
	
    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file("/dev/null", 'r')
    so = file("/dev/null", 'a+')
    se = file("/dev/null", 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    return True


def getMeminfo():
    lines = readFile("/proc/meminfo", lines=True)
    re_parser = re.compile(r'^(?P<key>\S*):\s*(?P<value>\d*)\s*kB' )
    result = {}
    for line in lines:
        match = re_parser.match(line)
        if not match:
            continue # skip lines that don't parse
        key, value = match.groups(['key', 'value'])
        result[key] = int(value)
    result['MemUsed'] = (result['MemTotal'] - result['MemFree'] - result['Buffers'] - result['Cached'])
    return result


def _getCpuStatList():
    lines = readFile("/proc/stat", lines=True)
    if not lines:
        return None
    return map(float, lines[0].split()[1:5])


def getCpuUsageAvg():
    st1 = _getCpuStatList()
    #time1 = time.time()
    time.sleep(1)
    st2 = _getCpuStatList()
    #time2 = time.time()
    if not (st1 and st2):
        return None
    usageTime = (st2[0] - st1[0]) + (st2[1] - st1[1]) + (st2[2] - st1[2])
    try:
        return (100.0 * usageTime) / (usageTime + (st2[3] - st1[3]))
    except ZeroDivisionError, e:
        return 0


def convertKbToMb(kb):
    return kb / 1024.0


def getDeviceFormatStatusFile(device):
    return "/var/tmp/format_%s.status" % device.replace('/', '_')


def getDeviceFormatLockFile(device):
    return "/var/lock/format_%s.lock" % device.replace('/', '_')


def getDeviceFormatOutputFile(device):
    return "/var/tmp/format_%s.out" % device.replace('/', '_')


def getGlusterVersion():
    rv = runCommand("/usr/sbin/gluster --version", output=True)
    if rv["Stderr"]:
        return None
    if rv["Status"] != 0:
        return None
    if not rv["Stdout"]:
        return None
    return rv["Stdout"].strip().split()[1]


def getCifsUserUid(userName):
    lines = readFile(Globals.CIFS_USER_FILE, lines=True)
    for line in lines:
        if not line.strip():
            continue
        tokens = line.strip().split(":")
        if tokens[1] == userName:
            return int(tokens[0])
    return None

def grunOfOutput(serverFile, command, argumentList=[]):
    output = []
    commandList = ["%s/%s" % (commandPath, command)] + argumentList
## junli.li - get rid of white lines
    serverNameListTmp = readFile(serverFile, lines=True)
    serverNameList = []
    for serverName in serverNameListTmp:
        if serverName.strip():
            serverNameList.append(serverName)
    if not serverNameList:
        return []
    status = True
    for serverName in serverNameList:
        rv = runCommand(sshCommandPrefix + [serverName.strip()] + commandList, output=True)
#        if rv["Status"] != 0:
#            sys.stderr.write("%s: %s\n" % (serverName.strip(), rv["Status"]))
#            sys.stderr.write("Stdout:\n%s\n" % rv["Stdout"])
#            sys.stderr.write("Stderr:\n%s\n" % rv["Stderr"])
#            sys.stderr.write("---\n")
#            status = False
#        else :
# junli.li - only get the bricks info from good nodes
	if rv["Status"] == 0:
	    output = output + eval(rv["Stdout"])

#    if status:
    return output
#    else:
#        return 2


def grun(serverFile, command, argumentList=[]):
    commandList = ["%s/%s" % (commandPath, command)] + argumentList
## junli.li - get rid of white lines
    serverNameListTmp = readFile(serverFile, lines=True)
    serverNameList = []
    for serverName in serverNameListTmp:
        if serverName.strip():
            serverNameList.append(serverName)

    if not serverNameList:
        return 1
    status = True
    for serverName in serverNameList:
        rv = runCommand(sshCommandPrefix + [serverName.strip()] + commandList, output=True)
        if rv["Status"] != 0:
            sys.stderr.write("%s: %s\n" % (serverName.strip(), rv["Status"]))
            sys.stderr.write("Stdout:\n%s\n" % rv["Stdout"])
            sys.stderr.write("Stderr:\n%s\n" % rv["Stderr"])
            sys.stderr.write("---\n")
            status = False

    if status:
        return 0
    else:
        return 2

def grunAddCifsUser(serverFile, command, argumentList):
    commandList = "%s/%s" % (commandPath, command) + " " + argumentList[0] + " " + argumentList[1] + " " + "`cat " +  argumentList[2] + "`"
## junli.li - get rid of white lines
    serverNameListTmp = readFile(serverFile, lines=True)
    serverNameList = []
    for serverName in serverNameListTmp:
        if serverName.strip():
            serverNameList.append(serverName)

    if not serverNameList:
        return 1
    status = True
    for serverName in serverNameList:
        rv = runCommand(sshCommandPrefixShell + " " + serverName.strip() + " " + commandList , shell=True, output=True)
        if rv["Status"] != 0:
            sys.stderr.write("%s: %s\n" % (serverName.strip(), rv["Status"]))
            sys.stderr.write("Stdout:\n%s\n" % rv["Stdout"])
            sys.stderr.write("Stderr:\n%s\n" % rv["Stderr"])
            sys.stderr.write("---\n")
            status = False
    if status:
        return 0
    else:
        return 2

def grunChangeCifsUserPasswd(serverFile, command, argumentList):
    commandList = "%s/%s" % (commandPath, command) + " " + argumentList[0] + " `cat " +  argumentList[1] + "`"
## junli.li - get rid of white lines
    serverNameListTmp = readFile(serverFile, lines=True)
    serverNameList = []
    for serverName in serverNameListTmp:
        if serverName.strip():
            serverNameList.append(serverName)

    if not serverNameList:
        return 1
    status = True
    for serverName in serverNameList:
        rv = runCommand(sshCommandPrefixShell + " " + serverName.strip() + " " + commandList , shell=True, output=True)
        if rv["Status"] != 0:
            sys.stderr.write("%s: %s\n" % (serverName.strip(), rv["Status"]))
            sys.stderr.write("Stdout:\n%s\n" % rv["Stdout"])
            sys.stderr.write("Stderr:\n%s\n" % rv["Stderr"])
            sys.stderr.write("---\n")
            status = False

    if status:
        return 0
    else:
        return 2

def getFileSystemType():
    return [os.path.basename(i).split('.')[1] for i in glob.glob("/sbin/mkfs.*")]

##########added by bin.liu 2013-4-27
def executeOnServer(serverName,commandWithArgs):
    if isLocalHost(serverName) == True:
        (status, message) = commands.getstatusoutput(commandWithArgs)
        if status:
            return 1, message
        return status,message
    output = ''
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    except Exception,e:
        return -2,'Error when using pub key to connect remote host [%s]' % str(e)
    try:
        key = paramiko.RSAKey.from_private_key_file(Globals.PKEYFILE)
        ssh.connect(serverName, Globals.PORT, Globals.USERNAME, pkey=key)
        stdin,stdout,stderr = ssh.exec_command(commandWithArgs)
        output = stdout.read()
        ssh.close()
        strerr = stderr.read()
        if strerr is None or strerr.strip() is '':
            return 0,output
        return 1,strerr
    except Exception,e:
        return -1,"cannot connect " + serverName +': '+ str(e)

def executeWithPasswd(serverName,cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
    except Exception,e:
        return -2, 'Error when using pub key to connect remote host %s' % str(e)
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(serverName, Globals.PORT, Globals.USERNAME,Globals.DEFAULT_PASSWD)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        ret = stdout.read()
        strerr = stderr.read()
        if strerr is None or strerr.strip() is '':
            return 0,ret
        return 1, strerr
    except Exception,e:
        return -1,'can not connect to server [%s]:%s' % serverName, str(e)

def installPubKey(serverName):
    if isLocalHost(serverName):
        return '0', 'local host'
    if os.path.exists(Globals.PUBKEYFILE)==False:
        return '26060', Globals.PUBKEYFILE + ' does not exist.'
    key = os.popen('cat ' + Globals.PUBKEYFILE).read()
    key = key.replace('\n',' ')
    cmd = '''echo ''' + key + ''' >> ''' + Globals.SSH_AUTHORIZED_KEYS_PATH_REMOTE
 
    status,output = executeWithPasswd(serverName,cmd)
    if status == -1:
        return '26104', output
    elif status == -2:
        return '26059', 'Error when using pub key to connect remote server [%s].[%s]' % serverName, output
    elif status == 1:
        return '26062', 'error when installing keys on server [%s]. %s'  % serverName, output
    return '0',''
  
def isOnline(serverName):
    hostName = os.popen("hostname").read()
    if hostName.strip() == serverName:
        return True
    port = 22
    username = 'root'
    pkey_file = Globals.PKEYFILE
    try:
        key = paramiko.RSAKey.from_private_key_file(pkey_file)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.connect(serverName, Globals.PORT, Globals.USERNAME,Globals.DEFAULT_PASSWD)
        return  True
    except Exception,e:
        return False

def errorCode(code, msg, params):
    responseDom = XmlHandler.ResponseXml()
    errorTag = responseDom.appendTagRoute("error")
    errorTag.appendChild(responseDom.createTag("code",code))
    errorTag.appendChild(responseDom.createTag("msg",msg))

    if params is not None:
        for param in params:
	           errorTag.appendChild(responseDom.createTag("param",param))
    return errorTag.toxml()

def isEmpty(var):
    if var is None:
        return True
    elif str(var).strip() is '':
        return True
    return False

def isLocalHost(serverName):
    hostName = os.popen('hostname').read().split('\n')[0]
    stats, ip = getLocal_IP()
    host = os.popen('cat /etc/hosts | grep ' + ip.strip()).read()
    if (serverName.strip() == hostName.strip()) or \
    (serverName.strip() == 'localhost') or \
    (serverName.strip() == '127.0.0.1') or \
    (ip == serverName):
        return True
    return False

def isIPAddr(serverName):
    ip="\\b((?!\\d\\d\\d)\\d+|1\\d\\d|2[0-4]\\d|25[0-5])\\.((?!\\d\\d\\d)\\d+|1\\d\\d|2[0-4]\\d|25[0-5])\\.((?!\\d\\d\\d)\\d+|1\\d\\d|2[0-4]\\d|25[0-5])\\.((?!\\d\\d\\d)\\d+|1\\d\\d|2[0-4]\\d|25[0-5])\\b"
    if re.match(ip,serverName) is None:
        return False
    return True

def getIPByName(serverName):
    if isIPAddr(serverName):
        return serverName
    return os.popen('cat /etc/hosts | grep ' + serverName).read().replace('\t',' ').split(' ')[0]

def getHosts(serverName):
    cmd = 'gluster peer status|grep Hostname'
    status,output = executeOnServer(serverName ,cmd)
    if status:
        return status, output
    list = output.split('\n')
    hosts = []
    hosts.append(serverName)
    for str1 in list:
        lst = str1.split(':')
        if len(lst)==2:
            status, host = executeOnServer(serverName,'cat /etc/hosts | grep ' + lst[1])
            if status:
                return status, host
            if host is None or host.strip() is '':
                continue
            hostName = host.replace('\t',' ').split(' ')[1]
            hosts.append(hostName)
        else:
            break
    return 0,hosts

def getLocal_IP():
    cmd = "ifconfig|grep inet|grep -v inet6|grep Bcast|cut -d ':' -f2|cut -d ' ' -f1|awk 'NR==1'"
    status,output = commands.getstatusoutput(cmd)
    return status,output

def rebalanceTaskStart(clusterName, volumeName):
    references = volumeName
    descriptions = 'Volume ' + volumeName + ' Rebalance'
    operationid = 3
    try:
        Globals.db.insert('task_info', reference=references, description=descriptions, operation_id=operationid, cluster_name=clusterName)
    except Exception,e:
        return (1, str(e))
    return (0, 'inserted into DB')

def getRebalanceStatus(output):
    if re.match('^rebalance completed.*', output) != -1:
        code = Globals.STATUS_CODE_SUCCESS
        message = 'rebalance completed'
    elif re.match('.*in progress.*', output) != -1:
        code = Globals.STATUS_CODE_RUNNING
        message = 'rebalance is running'
    else:
        code = Globals.STATUS_CODE_FAILURE
        message = 'rebalance failed'
    return code,message

def getInitialStatus(output):
    if re.match('STATUS_CODE_SUCCESS', output):
        code = Globals.STATUS_CODE_SUCCESS
        message = 'initialize disk successfully'
    elif re.match('STATUS_CODE_RUNNING', output):
        code = Globals.STATUS_CODE_RUNNING
        message = 'initializing disk is running'
    elif re.match('STATUS_CODE_FAILURE', output):
        code = Globals.STATUS_CODE_FAILURE
        message = 'initialize disk failed'
    else:
        code = Globals.STATUS_CODE_FAILURE
        message = 'initialize disk failed'
    return code,message

def getMigrateStatus(message):
    if re.match("^Number of files migrated.*Migration complete$",message) and re.match("^Number of files migrated = 0 .*Current file="):
        code = Globals.STATUS_CODE_COMMIT_PENDING
        return code,message
    elif re.match("^Number of files migrated.*Current file=.*",message):
        code = Globals.STATUS_CODE_RUNNING
        return "Brick Migration Started."
    elif re.match("^replace brick has been paused.*",message) :
        code = Globals.STATUS_CODE_PAUSE
        return code,"Brick Migration Paused"
    elif re.match("replace-brick not started on volume*",message):
        code = Globals.STATUS_CODE_SUCCESS
        return code,"Brick Migration Committed."
    else:
        code = Globals.STATUS_CODE_FAILURE
        return code,message
