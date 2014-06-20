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
import commands

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: %s USERNAME\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    userName = sys.argv[1]

### junli.li  force to delete user, even it is logged in
##  if Utils.runCommand("id %s" % userName) == 0:
# forbidden deleting system user
    status,output = commands.getstatusoutput("id  %s" % userName)
    if status == 0 and output.startswith("uid=1024"):
        if Utils.runCommand("userdel -f %s" % userName) != 0:
            Utils.log("failed to remove user name:%s\n" % userName)
            sys.stderr.write("Failed to remove user name:%s\n" % userName)
            sys.exit(1)
# make sure group deleted
    status,output = commands.getstatusoutput("cat /etc/group | grep %s" % userName)
    if status == 0 and output.startswith("%s:x:1024" % userName):
        if Utils.runCommand("groupdel %s" % userName) != 0:
            Utils.log("failed to remove group:%s\n" % userName)
            sys.stderr.write("Failed to remove group:%s\n" % userName)
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
