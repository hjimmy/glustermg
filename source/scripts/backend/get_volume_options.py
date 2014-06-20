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
from optparse import OptionParser
import commands

def getVolumeOptions(volumeName, option = None):
    cmd = 'gluster volume info ' + volumeName
    (status, output) = commands.getstatusoutput(cmd)
    if status:
        return output
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
    if type(options) != type({}):
        return options

    for option in options.keys():
        optionTag = responseDom.createTag("option",None)
        optionsTag.appendChild(optionTag)
        optionTag.appendChild(responseDom.createTag("key",option))
        optionTag.appendChild(responseDom.createTag("value",options[option]))
        
    return optionsTag.toxml()

def main():
    name = None
    if len(sys.argv) < 2:
        return 'volumename is required\n'
    option = None
    if len(sys.argv) == 2 or len(sys.argv) > 2:
        name = sys.argv[1]
    if len(sys.argv) > 2:
        option = sys.argv[2]
    if name is None or name.strip() is '':
        return 'volume is NULL'
    responseXml = getOptionDom(name, option)
    if responseXml:
        print responseXml
    sys.exit(0)

if __name__ == "__main__":
    main()
    
        