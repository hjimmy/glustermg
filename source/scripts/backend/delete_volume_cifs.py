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
    if len(sys.argv) != 2:
        sys.stderr.write("usage: %s VOLUME_NAME\n" % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    volumeName = sys.argv[1]

    volumeMountDirName = "%s/%s" % (Globals.REEXPORT_DIR, volumeName)
    try:
        if os.path.exists(volumeMountDirName):
            os.rmdir(volumeMountDirName)
    except OSError, e:
        Utils.log("failed deleting %s: %s\n" % (volumeMountDirName, str(e)))
        sys.stderr.write("Failed deleting %s: %s\n" % (volumeMountDirName, str(e)))
        sys.exit(1)

    if VolumeUtils.removeVolumeCifsConfiguration(volumeName):
        sys.exit(0)
    sys.stderr.write("Unable to remove volume cifs configuration\n")
    sys.exit(2)


if __name__ == "__main__":
    main()
