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
# 2012-03-22 junli.li <junli.li@cs2c.com.cn>
# add writelist and readlist in the smbconf file of volume
#

import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
import Globals
import Utils
import VolumeUtils
import getopt

def main():
    if len(sys.argv) < 3:
        sys.stderr.write("usage: %s VOLUME_NAME OWNER HOSTALLOWED\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)
  
    volumeName = sys.argv[1]
    owner = sys.argv[2]
    hostAllowed = sys.argv[3]

    volumeMountDirName = "%s/%s" % (Globals.REEXPORT_DIR, volumeName)
    try:
        if not os.path.exists(volumeMountDirName):
            os.mkdir(volumeMountDirName)
#   junli.li change mod of volumeMountDirName to 777, then, writeusers can write to this dir
        os.system('chmod 777 ' + volumeMountDirName)
    except OSError, e:
        Utils.log("failed creating %s: %s\n" % (volumeMountDirName, str(e)))
        sys.stderr.write("Failed creating %s: %s\n" % (volumeMountDirName, str(e)))
        sys.exit(1)

#   add arguments to writeVolumeCifsConfiguration()   junli.li
#   if not VolumeUtils.writeVolumeCifsConfiguration(volumeName, userList):
    if not VolumeUtils.writeVolumeCifsConfiguration(volumeName, owner, hostAllowed):
        sys.stderr.write("Failed to write volume cifs configuration\n")
        sys.exit(2)

    if Utils.runCommand("service smb reload") != 0:
        Utils.log("Failed to reload smb service")
        sys.stderr.write("Failed to reload smb service\n")
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
