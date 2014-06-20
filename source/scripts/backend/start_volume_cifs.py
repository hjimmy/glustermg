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
import Globals
import Utils
import VolumeUtils

def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: %s VOLUME_NAME KNOWN_SERVER\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    volumeName = sys.argv[1]
    serverName = sys.argv[2]

    volumeMountDirName = "%s/%s" % (Globals.REEXPORT_DIR, volumeName)
    cifsDirName = "%s/%s" % (Globals.CIFS_EXPORT_DIR, volumeName)

    if Utils.runCommand("mount -t glusterfs %s:%s %s" % (serverName, volumeName, volumeMountDirName)) != 0:
        Utils.log("Failed to mount volume %s" % (volumeName))
        sys.stderr.write("Failed to mount volume %s\n" % (volumeName))
        sys.exit(1)
    if Utils.runCommand("chown -R nobody:nobody %s" % (volumeMountDirName)) != 0:
        Utils.log("Failed to chown %s to nobody:nobody" % (volumeMountDirName))
        sys.stderr.write("Failed to chown %s to nobody:nobody" % (volumeMountDirName))
        sys.exit(5)
    if Utils.runCommand("chmod -R 777 %s" % (volumeMountDirName)) != 0:
        Utils.log("Failed to chmod %s to 777" % (volumeMountDirName))
        sys.stderr.write("Failed to chmod %s to 777" % (volumeMountDirName))
        sys.exit(6)
    if Utils.runCommand("ln -fTs %s %s" % (volumeMountDirName, cifsDirName)) != 0:
        Utils.log("Failed to create reexport link %s" % cifsDirName)
        sys.stderr.write("Failed to create reexport link %s\n" % cifsDirName)
        sys.exit(2)
    if Utils.runCommand("chown -R nobody:nobody %s" % (cifsDirName)) != 0:
        Utils.log("Failed to chown %s to nobody:nobody" % cifsDirName)
        sys.stderr.write("Failed to chown %s to nobody:nobody\n" % cifsDirName)
        sys.exit(7)
    if Utils.runCommand("/usr/sbin/selinuxenabled") == 0:
        if Utils.runCommand("chcon -t samba_share_t %s -h" % cifsDirName) != 0:
            Utils.log("Failed to change security context for the link %s" % cifsDirName)
            sys.stderr.write("Failed to change security context for the link %s\n" % cifsDirName)
            sys.exit(2)
    if not VolumeUtils.includeVolume(volumeName):
        Utils.log("Failed to include volume for CIFS reexport")
        sys.stderr.write("Failed to include volume for CIFS reexport\n")
        sys.exit(3)
    if Utils.runCommand("service smb reload") != 0:
        Utils.log("Failed to reload smb service")
        sys.stderr.write("Failed to reload smb service\n")
        sys.exit(4)
    sys.exit(0)


if __name__ == "__main__":
    main()
