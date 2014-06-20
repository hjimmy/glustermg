#!/usr/bin/python
#  Copyright (C) 2012 CS2C, Inc. <http://cs2c.com.cn>
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
#  junli.li <junli.li@cs2c.com.cn>
#  Change password of smbuser on Servers
#
import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
import grp
import pwd
import Globals
import Utils

def main():
    if len(sys.argv) < 3:
        sys.stderr.write("usage: %s USERNAME PASSWORD\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    userName = sys.argv[1]
    password = sys.argv[2]

    try:
        userInfo = pwd.getpwnam(userName)
    except KeyError, e:
        Utils.log("Failed to change password of user %s\n" % (userName))
        sys.stderr.write("Failed to change password of user %s\n" % (userName))
        sys.exit(4)

    if Utils.runCommand("smbpasswd -s %s" % userName,
                  input="%s\n%s\n" % (password, password)) != 0:
        Utils.log("failed to change smbpassword of user %s\n" %  userName)
        sys.stderr.write("Failed to change smbpassword of user %s\n" %  userName)
        sys.exit(5)
    sys.exit(0)


if __name__ == "__main__":
    main()
