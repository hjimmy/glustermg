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
#  2012-03-23 junli.li <junli.li@cs2c.com.cn>
#  update the cifs volume configuration
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
#import getopt module
import getopt

def usage():
    print ''' up_volume_cifs_all.py SERVER_FILE VOLUME_NAME [option][value]...
        -h or --help
        -a or --adminusers="admin users,using ',' split users"
        -w or --writeusers="users that can write to this volume, using ',' split users"
        -r or --readusers="users that can read this volume, using ',' split users"
              --hostsallowed="hostname that can access this volume, using ',' split hostname"
    '''
    return 0


def updateVolumeCifsConf(volumeName, userList):
    lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
    exists = 0 
    try:
        fp = open(Globals.CIFS_VOLUME_FILE, "r")
####  get the start_line  junli.li
        for line in lines:
            if not line.strip():
                continue
            if line.strip() == "["+volumeName+"]":
                start_line = lines.index(line)
		exists = 1
		break
####  whether the volume exists?  junli.li
	if exists == 0:
	    sys.stderr.write("%s volume does not exist\n" % (volumeName))
            sys.exit(10)
	fp.close()
###   modify the Globals.CIFS_VOLUME_FILE file. 
###   Firstly, delete the lines between start_line and start_line+3; then, add the new configuration information
###   junli.li
	fp = open(Globals.CIFS_VOLUME_FILE, "w")    
	lineNo = 0
	for eachline in lines:
	    if lineNo < start_line:
		fp.write(eachline)
	    elif lineNo > start_line + 4:
		fp.write(eachline)
	    lineNo = lineNo + 1
        fp.write("[%s]\n" % (volumeName))
	fp.write("  shared      = no\n")
        fp.write("  admin users = %s\n" % (userList['adminusers']))
        fp.write("  write users = %s\n" % (userList['writeusers']))
        fp.write("  read  users = %s\n" % (userList['readusers']))

        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_VOLUME_FILE, str(e)))
        return False
    return True


def main():
    if len(sys.argv) < 4:
        usage()
        sys.exit(-1)

    serverFile = sys.argv[1]
    volumeName = sys.argv[2]

### get the opts  junli.li
    shortargs = 'ha:w:r:'
    longargs = ['help','adminusers=','writeusers=','readusers=','hostsallowed=']

    opts, args = getopt.getopt( sys.argv[3:], shortargs, longargs )
    userList = {'adminusers':"", 'validusers':[], 'writeusers':"", 'readusers':"" }
    allowhosts = "*"
    for opt,val in opts:
        if opt in ( '-h', '--help' ):
            usage()
            sys.exit(0)
        if opt in ( '-a', '--adminusers' ):
            userList['adminusers'] = val
            continue
        if opt in ( '-w', '--writeusers' ):
            userList['writeusers'] = val
            continue
        if opt in ( '-r', '--readusers' ):
            userList['readusers'] = val
            continue
	if opt in ( '--hostsallowed' ):
	    allowhosts == val
	    continue

###  get the valid users  junli.li
    validusers = userList['adminusers'] + "," + userList['writeusers'] + "," + userList['readusers']
    tokens = validusers.strip().split(",")
    for userName in tokens:
        if userName not in userList['validusers'] and len(userName) != 0:
            userList['validusers'].append(userName)
    missingUserList = []
    for userName in userList['validusers']:
        if not Utils.getCifsUserUid(userName):
            missingUserList.append(userName)

    if missingUserList:
        sys.stderr.write("User %s does not exists\n" % missingUserList)
        sys.exit(1)

    rv = Utils.grun(serverFile, "update_volume_cifs.py", [volumeName] + sys.argv[3:])
    if rv == 0:
        if not updateVolumeCifsConf(volumeName, userList):
            sys.stderr.write("Failed to update volume %s and user-list %s in cifs volume configuration\n" % (volumeName, userList))
            sys.exit(11)
    sys.exit(rv)


if __name__ == "__main__":
    main()
