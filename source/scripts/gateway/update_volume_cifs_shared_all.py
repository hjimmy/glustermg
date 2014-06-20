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
    print ''' update_volume_cifs_shared_all.py SERVER_FILE VOLUME_NAME 
    '''
    return 0


def updateVolumeCifsConf(volumeName):
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
	fp.write("  shared      = yes\n")
        fp.write("  admin users = \n")
        fp.write("  write users = \n")
        fp.write("  read  users = \n")

        fp.close()
    except IOError, e:
        Utils.log("failed to write file %s: %s" % (Globals.CIFS_VOLUME_FILE, str(e)))
        return False
    return True


def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(-1)

    serverFile = sys.argv[1]
    volumeName = sys.argv[2]
    allowhosts = "*"
    if len(sys.argv) == 4:
	allowhosts = sys.argv[3]

    rv = Utils.grun(serverFile, "update_volume_cifs_shared.py", [volumeName] + sys.argv[3:])
    if rv == 0:
        if not updateVolumeCifsConf(volumeName):
            sys.stderr.write("Failed to update volume %s in cifs volume configuration\n" % (volumeName))
            sys.exit(11)
    sys.exit(rv)


if __name__ == "__main__":
    main()
