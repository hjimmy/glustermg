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

def getVolumeBricks(volumeName, brick = None):
    cmd = 'gluster volume info ' + volumeName
    (status, output) = commands.getstatusoutput(cmd);
    
    if status != 0:
        return 1,output
    bricksprefix = 'Bricks'
    brickfound = False
    volumeinfo = output.split('\n')
    Dict = []
    
    for info in volumeinfo:
        if info.startswith('Volume') == True or info.startswith('Type') == True or info.startswith('Status') == True or \
        info.startswith('Number') == True or info.startswith('Transport') == True or info.startswith('Options Reconfigured') == True:
            brickfound = False
            continue
        if info.startswith(bricksprefix) == True:
            brickfound = True
            continue 
        if brickfound == False:
            continue
        list = info.split(':',1)
        if len(list) !=2:
            brickfound = False
        Dict.append(list[1])
    return 0,Dict

def main():
    name = None
    if len(sys.argv) < 2:
        return 'volumename is required\n'
    option = None
    if len(sys.argv) == 2 or len(sys.argv) > 2:
        name = sys.argv[1]
    if len(sys.argv) > 2:
        option = sys.argv[2] 
    status, output = getVolumeBricks(name, option)
    if status:
        print output
        sys.exit(status)
    for e in output:
        print e
    return list

    sys.exit(status)

if __name__ == "__main__":
    main()
