#!/usr/bin/python
#  Copyright (C) 2012 CS2C, Inc. <http://www.cs2c.com.cn>
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
# junli.li <junli.li@cs2c.com.cn>
# change password of cifsuser
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


def getUid(userName):
    lines = Utils.readFile(Globals.CIFS_USER_FILE, lines=True)
    for line in lines:
        tokens = line.strip().split(":")
        if tokens[1] == userName:
            return int(tokens[0])
    return None

def main():
    if len(sys.argv) < 4:
        sys.stderr.write("usage: %s SERVER_FILE USERNAME PASSWORD_FILE\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    serverFile = sys.argv[1]
    userName = sys.argv[2]
    passwordFile = sys.argv[3]

    uid = getUid(userName)
    if not uid:
        sys.stderr.write("cifsser %s not exist in %s\n" % (userName,Globals.CIFS_USER_FILE))
        sys.exit(10)

    rv = Utils.grunChangeCifsUserPasswd(serverFile, "change_passwd_user_cifs.py", ["%s" % userName, passwordFile])

    if rv != 0:
        sys.stderr.write("Failed to change password of this user\n")
        sys.exit(rv)
    sys.exit(0)


if __name__ == "__main__":
    main()
