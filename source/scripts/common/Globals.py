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
import web
import memcache

MULTICAST_GROUP = '224.224.1.1'
MULTICAST_PORT  = 24729
GLUSTER_PROBE_STRING = "GLUSTERPROBE"
GLUSTER_PROBE_VERSION = "2.4.0"
DEFAULT_BUFSIZE = 1024
SERVER_PORT = 24731
DEFAULT_BACKLOG = 5
DEFAULT_TIMEOUT = 3
DEFAULT_ID_LENGTH = 16
GLUSTER_PLATFORM_VERSION = "3.2"

###########added by bin.liu
db = web.database(dbn='mysql', db='webpy', user='gluster', pw='neokylin123')
mc = memcache.Client(['127.0.0.1:12333'])
BACKEND_SCRIPT = '/opt/glustermg/2.4/backend/'
SSH_AUTHORIZED_KEYS_DIR_LOCAL = "/opt/glustermg/keys/"
SSH_AUTHORIZED_KEYS_DIR_REMOTE = "/root/.ssh/"
SSH_AUTHORIZED_KEYS_PATH_REMOTE = SSH_AUTHORIZED_KEYS_DIR_REMOTE + 'authorized_keys'
PKEYFILE = SSH_AUTHORIZED_KEYS_DIR_LOCAL + 'gluster.pem'
PUBKEYFILE = SSH_AUTHORIZED_KEYS_DIR_LOCAL + 'gluster.pub'
LOG_CONF = BACKEND_SCRIPT + "logging.conf"
USERNAME = 'root'
PORT = 22
DEFAULT_PASSWD = 'neokylin123'
STATUS_CODE_SUCCESS = 0
STATUS_CODE_FAILURE = 1
STATUS_CODE_PART_SUCCESS = 2
STATUS_CODE_RUNNING = 3
STATUS_CODE_PAUSE = 4
STATUS_CODE_WARNING = 5
STATUS_CODE_COMMIT_PENDING = 6
STATUS_CODE_ERROR = 7
VOLUME_TYPE_STR = ["distribute", "replicate", "distributed replicate","stripe", "distributed stripe"]
VOLUME_LOG_TYPE = ['EMERGENCY', 'ALERT', 'CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG', 'TRACE', 'ALL']
TMP_LOG_DIR = '/tmp/bricklog/'
BRICK_LOG_DIR = '/var/log/glusterfs/bricks/'
## System configuration constants
SYSCONFIG_NETWORK_DIR  = "/etc/sysconfig/network-scripts"
FSTAB_FILE             = "/etc/fstab"
SAMBA_CONF_FILE        = "/etc/samba/smb.conf"
REAL_SAMBA_CONF_FILE   = "/etc/samba/real.smb.conf"
MODPROBE_CONF_FILE     = "/etc/modprobe.d/bonding.conf"
RESOLV_CONF_FILE       = "/etc/resolv.conf"
VOLUME_USER_DESCRIPTION   = "Gluster Volume User"
GLUSTER_BASE_DIR          = "/etc/glustermg"
REEXPORT_DIR              = "/reexport"
CIFS_EXPORT_DIR           = "/cifs"
SERVERS_FILE		  = "/opt/glustermg/etc/servers.cifs"

## Derived constants
VOLUME_CONF_DIR    = GLUSTER_BASE_DIR + "/volumes"
VOLUME_SMBCONF_FILE = VOLUME_CONF_DIR + "/volumes.smbconf.list"

AWS_WEB_SERVICE_URL = "http://169.254.169.254/latest"
DEFAULT_UID = 1024000
CIFS_USER_FILE = "/opt/glustermg/etc/users.cifs"
CIFS_VOLUME_FILE  = "/opt/glustermg/etc/volumes.cifs"
