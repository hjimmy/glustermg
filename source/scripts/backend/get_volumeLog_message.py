import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
import socket
import re
import Utils
import DiskUtils
import NetworkUtils
import XmlHandler
import commands
import time
import xml.etree.ElementTree
import datetime
import XmlHandler

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

LOG_DIR = '/var/log/glusterfs/bricks/'


 
def getBrickLogs(brick,linecount):
    server_dir = brick.split(':/')
    LOGFILE = LOG_DIR + server_dir[1] + '.log'
    cmd = 'python /root/gmc-rewrite/gmc-webpy/gmc-webpy/backend/get_volume_brick_log.py ' + LOGFILE + ' ' + str(linecount)
    status,output = commands.getstatusoutput(cmd)
    if status != 0:
        return 'failed to get log'
    weblog = xml.etree.ElementTree.fromstring(output)
    volLogList = []
    for entry in weblog.findall("logMessage"):
        volumeLogMessage = VolumeLogMessage()
        volumeLogMessage.setBrick(brick)
        volumeLogMessage.setMessage(entry.find('message').text)
        volumeLogMessage.setSeverity(entry.find('severity').text)
        volumeLogMessage.setTimestamp(entry.find('timestamp').text)
        volLogList.append(volumeLogMessage)
    return volLogList

def filterServerity(volLogList,severity):
    for volumeLogMessage in volLogList:
        if volumeLogMessage.getSeverity().lower() != severity.lower():
            #print volumeLogMessage.getSeverity(), severity.lower()
            volLogList.remove(volumeLogMessage)
    return volLogList

def filterTimeStamp(volLogList, fromTimeStamp, toTimeStamp):
    fromTime = time.strptime(fromTimeStamp,'%Y-%m-%d %H:%M:%S')
    toTime = time.strptime(toTimeStamp,'%Y-%m-%d %H:%M:%S')
    
    for volumeLogMessage in volLogList:
        index = volumeLogMessage.getTimeStamp().index('.')
        if index == -1:
            theTime = time.strptime(volumeLogMessage.getTimeStamp()[:index], '%Y-%m-%d %H:%M:%S')
        else:
            theTime = time.strptime(volumeLogMessage.getTimeStamp(), '%Y-%m-%d %H:%M:%S')
        if theTime < fromTime or theTime > toTime:
            volLogList.remove(volumeLogMessage)
    return volLogList

def getMessageDom(volLogList):
    responseDom = XmlHandler.ResponseXml()
    logMessagesTag = responseDom.appendTagRoute("logMessages")
    
    for volumeLogMessage in volLogList:
        logMessageTag = responseDom.createTag("logMessage",None)
        logMessagesTag.appendChild(logMessageTag)
        logMessageTag.appendChild(responseDom.createTag("brick",volumeLogMessage.getBrick()))
        logMessageTag.appendChild(responseDom.createTag("message",volumeLogMessage.getMessage()))
        logMessageTag.appendChild(responseDom.createTag("severity",volumeLogMessage.getSeverity()))
        logMessageTag.appendChild(responseDom.createTag("timestamp",volumeLogMessage.getTimeStamp()))
    return logMessagesTag

def main():
    if len(sys.argv) < 3:
        print 'python get_volumeLog_message.py lineCount brickName'
        sys.exit(-1)
    lineCount = sys.argv[1]
    brickName = sys.argv[2] 

    severity = ''
    fromtime = ''
    totime = ''

    if len(sys.argv) > 3:
        severity = sys.argv[3]
    if len(sys.argv) > 4:
        fromtime = sys.argv[4]
    if len(sys.argv) > 5:
        totime = sys.argv[5]

    volLogList = getBrickLogs(brickName,lineCount)
    print len(volLogList)
    if severity.strip() != '':
        volLogList = filterServerity(volLogList,severity)
        print len(volLogList)
    if (fromtime.strip() != '') and (totime.strip() != ''):
        volLogList = filterTimeStamp(volLogList, fromtime, totime)
    responseXml = getMessageDom(volLogList)
    if responseXml:
       print responseXml.toxml()
    sys.exit(0)

if __name__ == "__main__":
    main()
