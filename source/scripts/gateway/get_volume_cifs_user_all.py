#!/usr/bin/python
# Copyright (C) 2012 CS2C, Inc, <http://www.cs2c.com.cn>
# This file is part of Gluster Management Gateway (GlusterMG).
#
# GlusterMG is free software; you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; 
#
# This file is used to get the cifs users information of a volume by xml.
# It has four types of users, ie, adimin users,valid users,writelist and 
# readlist.
#
# 2012-03-21 junli.li <junli.li@cs2c.com.cn>
# This python script is newly added by junli.li
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
import re

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: %s VOLUME_NAME \n" %os.path.basename(sys.argv[0]))
	sys.exit(-1) 

    volumeName = sys.argv[1]
    lines = Utils.readFile(Globals.CIFS_VOLUME_FILE, lines=True)
    linenum = 0
    volume_exist = False

    shared = "no"
    adminusers = ""
    writelist = ""
    readlist = ""
    for line in lines:
	m = re.match("\["+volumeName+"\]",line)
	if m is not None:
	    if lines[linenum + 1].strip().split(" = ")[0].strip() == "shared":
	        shared = lines[linenum + 1].strip().split(" = ")[1]	    
	    if lines[linenum + 2].strip().split(" = ")[0] == "admin users":
	        adminusers = (lines[linenum + 2].strip()).split(" = ")[1]
	    if lines[linenum + 3].strip().split(" = ")[0] == "write users":
	        writelist = lines[linenum + 3].strip().split(" = ")[1]
	    if lines[linenum + 4].strip().split(" = ")[0] == "read  users":
	        readlist = lines[linenum + 4].strip().split(" = ")[1]
	    volume_exist = True
	    break
	linenum = linenum + 1 
    
    if volume_exist == True:
	print "shared     : " + shared
	print "adminusers : " + adminusers
	print "writelist  : " + writelist
        print "readlist   : " + readlist
    else:
	print volumeName + " volume  does not exist or not belong to cifs type "
	    	
if __name__ == "__main__":
    main()
   

