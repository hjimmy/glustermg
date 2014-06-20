import web
import re
import base64
import json
import os
import sys
import time
import paramiko
import commands
import xml.etree.ElementTree
import Globals

p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/../scripts/common/" % (p1)
p3 = "%s/../services/" %(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
if not p3 in sys.path:
    sys.path.append(p3)

import XmlHandler
import Utils
import volumeService
import VolumeUtils

class VolumeLogMessage:
    def __init__(self, timestamp = None, brickDirectory = None, severity = None, message = None):
        self._brick = ''
        self._severity = ''
        self._message = ''
        self._timestamp = ''

    def getTimeStamp(self):
        return self._timestamp
    
    def setTimestamp(self, timestamp):
        self._timestamp = timestamp
    
    def getSeverity(self):
        return self._severity

    def setSeverity(self,severity):
        self._severity = severity;

    def getMessage(self):
        return self._message

    def setMessage(self,message):
        self._message = message;
    
    def setBrick(self, brick):
        self._brick = brick;

    def getBrick(self):
        return self._brick;

    def filter(self, filterString, caseSensitive):
        str = self.getSeverity() + self.getTimestamp() + self.getBrick() + self.getMessage()
        if caseSensitive:
            if str.index(filterString) > 0:
                return True
            return False
        else:
            if str.lower().index(filterString.lower()) > 0:
                return True
            return False

from Globals import *

def filterServerity(volLogList,severity):
    list = []
    for volumeLogMessage in volLogList:
        if volumeLogMessage.getSeverity().lower() != severity.lower():
            #print volumeLogMessage.getSeverity(), severity.lower()
            continue
        list.append(volumeLogMessage)
    return list

def filterTimeStamp(volLogList, fromTimeStamp, toTimeStamp):
#    fromTime = time.strptime(fromTimeStamp,'%Y-%m-%d %H:%M:%S')
#    toTime = time.strptime(toTimeStamp,'%Y-%m-%d %H:%M:%S')
    fromTime = time.strptime(fromTimeStamp,'%m/%d/%Y %H:%M:%S')
    toTime = time.strptime(toTimeStamp,'%m/%d/%Y %H:%M:%S')
    list = []
    for volumeLogMessage in volLogList:
        index = volumeLogMessage.getTimeStamp().index('.')
        if index != -1:
            theTime = time.strptime(volumeLogMessage.getTimeStamp()[:index], '%Y-%m-%d %H:%M:%S')
        else:
            theTime = time.strptime(volumeLogMessage.getTimeStamp(), '%Y-%m-%d %H:%M:%S')
        if theTime < fromTime or theTime > toTime:
            continue
        list.append(volumeLogMessage)
    return list

def getLogs(clusterName,volumeName, brickName,linecount='100', severity=None, fromTimeStamp=None, toTimeStamp=None):
    params = []
    params.append(clusterName)
    params.append(volumeName)
    params.append(brickName)
    params.append(linecount)
    params.append(severity)
    params.append(fromTimeStamp)
    params.append(toTimeStamp)
    web.header('Content-Type', 'application/xml')
    print severity

    if severity not in Globals.VOLUME_LOG_TYPE:
        code,reval = '23501','bad severity type:%s' % severity
        result = Utils.errorCode(code, reval, params)
        web.HTTPError(status = "400 Bad request", data = result)
        return result

    volLogList = []
    if (brickName is not None) and (brickName.strip() is not ''):
        server_dir = brickName.split(':/')
        if len(server_dir) == 2:
            file = server_dir[1].strip()
            log = file.replace('/', '-')
            LOGFILE = BRICK_LOG_DIR + log + '.log*'
            cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_brick_log.py ' + LOGFILE + ' ' + str(linecount)

            (status,output) = Utils.executeOnServer(server_dir[0].strip(), cmd)
            output.replace('\n',' ')
            if status == -1:
                code, reval = '26104', 'error when connecting to remote host ' + server_dir[0].strip() + ' from localhost:' + output
            elif status == -2:
                code,reval = '26059', 'Error when using pub key to connect remote server ' + server_dir[0].strip() + '.' + output
            elif status == 1:
                if re.match('volume log not found',output):
                    code, reval = '20053', 'volume ' + volumeName + ' does not exist.\n' + output
                    result = Utils.errorCode(code, reval, params)
                    web.HTTPError(status = "400 Bad request", data = result)
                    return result
                else:
                    code, reval = '23015', 'Error when executing "' + cmd + '".\n' + output
            if status:
                result = Utils.errorCode(code, reval, params)
                web.HTTPError(status = "400 Bad Request", data = '')
                return result
            weblog = xml.etree.ElementTree.fromstring(output) 
            for entry in weblog.findall("logMessage"):
                volumeLogMessage = VolumeLogMessage()
                volumeLogMessage.setBrick(brickName)
                volumeLogMessage.setMessage(entry.find('message').text)
                volumeLogMessage.setSeverity(entry.find('severity').text)
                volumeLogMessage.setTimestamp(entry.find('timestamp').text)
                volLogList.append(volumeLogMessage)
    else:
        cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_bricks.py ' + volumeName
        serverName = volumeService.getServerName(clusterName)
        (status,output) = Utils.executeOnServer(serverName, cmd)
        list = output.split(' ')
        if list[-1] == 'exist':
            result = Utils.errorCode('20053', 'volume ' + volumeName + ' does not exist', params)
            raise web.HTTPError(status='400 Bad Request', data=result)
        bricklist = output.split('\n')
        VolumeUtils.isExecSucess(status, output, serverName, volumeName, cmd, '23130', params)
        #if status == -1:
        #    code, reval = '26104', 'error when connecting to remote host [' + serverName + '] from localhost:' + output
        #elif status == -2:
        #    code,reval = '26059', 'Error when using pub key to connect remote server [' + serverName + '].' + output
        #elif status == 1:
        #    code, reval = '23019','Error when getting bricks from server [' + serverName + '].'
        #result = ''
        #if status:
        #    web.header('Content-Type', 'text/xml')
        #    result = Utils.errorCode(code, reval, [])
        #    web.HTTPError(status = "400 Bad Request", data = '')
        #    return result
        for brick in bricklist:
            server_dir = brick.split(':/')
            if len(server_dir) != 2:
                break
            file = server_dir[1].strip()
            log = file.replace('/', '-')
            LOGFILE = BRICK_LOG_DIR + log + '.log'
            cmd = 'python ' + BACKEND_SCRIPT + 'get_volume_brick_log.py ' + LOGFILE + ' ' + str(linecount)
            status,output = Utils.executeOnServer(server_dir[0].strip(), cmd) 
            if status == -1:
                code, reval = '26104', 'error when connecting to remote host ' + server_dir[0].strip() + ' from localhost:' + output
            elif status == -2:
                code,reval = '26059', 'Error when using pub key to connect remote server ' + server_dir[0].strip() + '.' + output
            elif status == 1:
                if re.match('exist', output):
                    code, reval = '20053', 'volume ' + volumeName + ' does not exist.\n' + output
                else:
                    code, reval = '23021', 'Error when executing "' + cmd + '".\n' + output
            if status:
                result = Utils.errorCode(code, reval, [])
                raise web.HTTPError(status = "400 Bad Request", data = result) 
            weblog = xml.etree.ElementTree.fromstring(output)
            
            for entry in weblog.findall("logMessage"):
                volumeLogMessage = VolumeLogMessage()
                volumeLogMessage.setBrick(brick)
                volumeLogMessage.setMessage(entry.find('message').text)
                volumeLogMessage.setSeverity(entry.find('severity').text)
                volumeLogMessage.setTimestamp(entry.find('timestamp').text)
                volLogList.append(volumeLogMessage)
    if (severity is not None) and (severity.strip() != '') and (severity.lower() != 'all'):
        volLogList = filterServerity(volLogList, severity)
    if (fromTimeStamp is not None) and (toTimeStamp is not None) and (fromTimeStamp is not '') and (toTimeStamp is not ''):
        volLogList = filterTimeStamp(volLogList, fromTimeStamp, toTimeStamp)
    responseDom = XmlHandler.ResponseXml()
    logMessagesTag = responseDom.appendTagRoute("logMessages")
    
    for volumeLogMessage in volLogList:
        logMessageTag = responseDom.createTag("logMessage",None)
        logMessagesTag.appendChild(logMessageTag)
        logMessageTag.appendChild(responseDom.createTag("brick",volumeLogMessage.getBrick()))
        logMessageTag.appendChild(responseDom.createTag("message",volumeLogMessage.getMessage()))
        logMessageTag.appendChild(responseDom.createTag("severity",volumeLogMessage.getSeverity()))
        logMessageTag.appendChild(responseDom.createTag("timestamp",volumeLogMessage.getTimeStamp()))
    return logMessagesTag.toxml()

def main():
    severity = ''
    fromtime = ''
    totime = ''
    lineCount = ''
    brickName = ''
    volumeName = 'test1'
    clusterName = 'cluster2'
    if len(sys.argv) > 1: 
        lineCount = sys.argv[1]
    if len(sys.argv) > 2:
        brickName = sys.argv[2]
    if len(sys.argv) > 3:
        volumeName = sys.argv[3]
    if len(sys.argv) > 4:
        fromtime = sys.argv[4]
    if len(sys.argv) > 5:
        totime = sys.argv[5]
    responseXml = getLogs(clusterName, volumeName,brickName.strip(),lineCount)
    
#     if severity.strip() != '':
#         volLogList = filterServerity(volLogList,severity)
#     if (fromtime.strip() != '') and (totime.strip() != ''):
#         volLogList = filterTimeStamp(volLogList, fromtime, totime)
#     responseXml = getMessageDom(volLogList)
#    if responseXml:
#        print responseXml
    print responseXml
    sys.exit(0)

if __name__ == "__main__":
    main()
