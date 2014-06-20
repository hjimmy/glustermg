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
import Utils

def getBrickSpace(BrickDir):
    server_dir = BrickDir.split(':')
    direct = server_dir[1]
    if (os.path.exists(direct)) and direct[:11] == '/neofs/data':
        rv = Utils.runCommand(['df', direct], output=True)
        total = (long(rv["Stdout"].split("\n")[-2].split()[-5])/1024.0)
        free = (long(rv["Stdout"].split("\n")[-2].split()[-3])/1024.0)
    else:
        total = 0.0
        free = 0.0
    return total,free

def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: %s VOLUME_NAME BRICK_NAME\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    volumeName = sys.argv[1]
    brickName = sys.argv[2]
    # glusterfs-3.3 config change from /etc/glusterd to /var/lib/glusterd
    pidFile = "/var/lib/glusterd/vols/%s/run/%s.pid" % (volumeName, brickName.replace(":", "").replace("/", "-"))
    total, free = getBrickSpace(brickName)
    if pidFile[-5] == '-':
        pidFile = pidFile[:-5]+pidFile[-4:]
    if not os.path.exists(pidFile):
        print "OFFLINE", total, free
        sys.exit(0)

    lines = Utils.readFile(pidFile)
    if not lines:
        print "UNKNOWN", total, free
        sys.exit(0)
    try:
        pidString = lines[0]
        os.getpgid(int(pidString))
        print "ONLINE", total, free
    except ValueError, e:
        Utils.log("invalid pid %s in file %s: %s" % (pidString, pidFile, str(e)))
        print "UNKNOWN", total, free
    except OSError, e:
        #Utils.log("failed to get process detail of pid %s: %s" % (pidString, str(e)))
        print "OFFLINE", total, free
    sys.exit(0)

if __name__ == "__main__":
    main()
