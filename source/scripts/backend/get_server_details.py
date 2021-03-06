#!/usr/bin/python
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
import socket
import re
import Utils
import DiskUtils
import NetworkUtils
import XmlHandler
from optparse import OptionParser


def getDiskDom():
    diskInfo = DiskUtils.getDiskInfo()
    if not diskInfo:
        return None
    procMdstat = DiskUtils.getProcMdstat()
    diskDom = XmlHandler.XDOM()
    disksTag = diskDom.createTag("disks", None)
    diskTagDict = {}
    for diskName, value in diskInfo.iteritems():
        diskTag = diskDom.createTag("disk", None)
        diskTag.appendChild(diskDom.createTag("name", diskName))
        diskTag.appendChild(diskDom.createTag("description", value["Description"]))
        diskTag.appendChild(diskDom.createTag("uuid", value["Uuid"]))
        if DiskUtils.isDiskInFormatting(diskName):
            status = "INITIALIZING"
        else:
            if value["FsType"]:
                status = "INITIALIZED"
            else:
                status = "UNINITIALIZED"
        diskTag.appendChild(diskDom.createTag("status", status))
        if value["MountPoint"] and value["MountPoint"] in ["/", "/boot"]:
            diskTag.appendChild(diskDom.createTag("type", "BOOT"))
        elif "UNINITIALIZED" == status:
            diskTag.appendChild(diskDom.createTag("type", "UNKNOWN"))
        elif "swap" == value["FsType"]:
            diskTag.appendChild(diskDom.createTag("type", "SWAP"))
        else:
            diskTag.appendChild(diskDom.createTag("type", "DATA"))
        diskTag.appendChild(diskDom.createTag("fsType", value["FsType"]))
        diskTag.appendChild(diskDom.createTag("fsVersion", value["FsVersion"]))
        diskTag.appendChild(diskDom.createTag("mountPoint", value["MountPoint"]))
        diskTag.appendChild(diskDom.createTag("size", value["Size"] / 1024.0))
        if not value["SpaceInUse"]:
            diskTag.appendChild(diskDom.createTag("spaceInUse", None))
        else:
            diskTag.appendChild(diskDom.createTag("spaceInUse", value["SpaceInUse"] / 1024.0))
        partitionsTag = diskDom.createTag("partitions", None)
        diskTag.appendChild(partitionsTag)
        for partName, partValues in value['Partitions'].iteritems():
            partitionTag = diskDom.createTag("partition", None)
            partitionTag.appendChild(diskDom.createTag("name", partName))
            partitionTag.appendChild(diskDom.createTag("uuid", partValues["Uuid"]))
## junli.li - bugfix 25903
	    if os.popen("fdisk -l 2>/dev/null |grep %s" % partName).read().upper().find("FAT") != -1:
		partValues["FsType"] = "fat"
            partitionTag.appendChild(diskDom.createTag("fsType", partValues["FsType"]))
            if partValues["MountPoint"] and partValues["MountPoint"] in ["/", "/boot"]:
                partitionTag.appendChild(diskDom.createTag("status", "INITIALIZED"))
                partitionTag.appendChild(diskDom.createTag("type", "BOOT"))
            elif partValues["FsType"]:
		if partValues["FsType"].upper().find("FAT") != -1:
		    partitionTag.appendChild(diskDom.createTag("status", "NOTUSE"))
                else:
		    partitionTag.appendChild(diskDom.createTag("status", "INITIALIZED"))
                if "swap" == partValues["FsType"]:
                    partitionTag.appendChild(diskDom.createTag("type", "SWAP"))
                else:
                    partitionTag.appendChild(diskDom.createTag("type", "DATA"))
            elif partValues["Size"] == 1:
		partitionTag.appendChild(diskDom.createTag("type", "EXTENDED"))
		partitionTag.appendChild(diskDom.createTag("status", "NOTUSE"))
            else:
                partitionTag.appendChild(diskDom.createTag("status", "UNINITIALIZED"))
                partitionTag.appendChild(diskDom.createTag("type", "UNKNOWN"))
            partitionTag.appendChild(diskDom.createTag("mountPoint", partValues['MountPoint']))
            partitionTag.appendChild(diskDom.createTag("size", partValues["Size"] / 1024.0))
            if not partValues["SpaceInUse"]:
                partitionTag.appendChild(diskDom.createTag("spaceInUse", None))
            else:
                partitionTag.appendChild(diskDom.createTag("spaceInUse", partValues["SpaceInUse"] / 1024.0))
            partitionsTag.appendChild(partitionTag)
            continue
        disksTag.appendChild(diskTag)
    diskDom.addTag(disksTag)
    return diskDom


def getServerDetails(listall):
    serverName = socket.getfqdn()
    meminfo = Utils.getMeminfo()
    cpu = Utils.getCpuUsageAvg()
    nameServerList, domain, searchDomain = NetworkUtils.readResolvConfFile()
    if not domain:
        domain = [None]

    responseDom = XmlHandler.ResponseXml()
    serverTag = responseDom.appendTagRoute("glusterServer")
    serverTag.appendChild(responseDom.createTag("name", serverName))
    serverTag.appendChild(responseDom.createTag("domainname", domain[0]))
    if Utils.runCommand("pidof glusterd") == 0:
        serverTag.appendChild(responseDom.createTag("status", "ONLINE"))
    else:
        serverTag.appendChild(responseDom.createTag("status", "OFFLINE"))
    serverTag.appendChild(responseDom.createTag("glusterFsVersion", Utils.getGlusterVersion()))
    serverTag.appendChild(responseDom.createTag("cpuUsage", str(cpu)))
    serverTag.appendChild(responseDom.createTag("totalMemory", str(Utils.convertKbToMb(meminfo['MemTotal']))))
    serverTag.appendChild(responseDom.createTag("memoryInUse", str(Utils.convertKbToMb(meminfo['MemUsed']))))
    serverTag.appendChild(responseDom.createTag("uuid", None))

    for dns in nameServerList:
        serverTag.appendChild(responseDom.createTag("dns%s" % str(nameServerList.index(dns) +1) , dns))

    #TODO: probe and retrieve timezone, ntp-server details and update the tags

    interfaces = responseDom.createTag("networkInterfaces", None)
    for deviceName, values in NetworkUtils.getNetDeviceList().iteritems():
        if values["type"] is None:
            continue
        if values["type"].upper() in ['LOCAL', 'IPV6-IN-IPV4']:
            continue
	if values["onboot"] and values["onboot"].upper() not in ['YES','"YES"', "'YES'"]:
	    continue
        if not values["onboot"]:
	    continue
        interfaceTag = responseDom.createTag("networkInterface", None)
        interfaceTag.appendChild(responseDom.createTag("name",  deviceName))
        interfaceTag.appendChild(responseDom.createTag("hwAddr", values["hwaddr"]))
        interfaceTag.appendChild(responseDom.createTag("speed", values["speed"]))
        interfaceTag.appendChild(responseDom.createTag("model", values["type"]))
        if values["onboot"]:
            interfaceTag.appendChild(responseDom.createTag("onBoot", values["onboot"]))
        else:
            interfaceTag.appendChild(responseDom.createTag("onBoot", "no"))
        interfaceTag.appendChild(responseDom.createTag("bootProto", values["bootproto"]))
        interfaceTag.appendChild(responseDom.createTag("ipAddress",    values["ipaddr"]))
        interfaceTag.appendChild(responseDom.createTag("netMask",   values["netmask"]))
        interfaceTag.appendChild(responseDom.createTag("defaultGateway",   values["gateway"]))
        if values["mode"]:
            interfaceTag.appendChild(responseDom.createTag("mode",   values["mode"]))
        if values["master"]:
            interfaceTag.appendChild(responseDom.createTag("bonding", "yes"))
            spliter = re.compile(r'[\D]')
            interfaceTag.appendChild(responseDom.createTag("bondid", spliter.split(values["master"])[-1]))
        interfaces.appendChild(interfaceTag)
    serverTag.appendChild(interfaces)

    responseDom.appendTag(serverTag)
    serverTag.appendChild(responseDom.createTag("numOfCPUs", int(os.sysconf('SC_NPROCESSORS_ONLN'))))

    diskDom = getDiskDom()
    if not diskDom:
        sys.stderr.write("No disk found!")
        Utils.log("Failed to get disk details")
        sys.exit(2)

    serverTag.appendChild(diskDom.getElementsByTagRoute("disks")[0])
    return serverTag

def main():
    parser = OptionParser()
    parser.add_option("-N", "--only-data-disks",
                      action="store_false", dest="listall", default=True,
                      help="List only data disks")

    (options, args) = parser.parse_args()
    responseXml = getServerDetails(options.listall)
    if responseXml:
        print responseXml.toxml()

    sys.exit(0)

if __name__ == "__main__":
    main()
