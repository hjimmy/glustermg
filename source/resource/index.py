import web
import commands
import os,sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/../" % (p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)

from scripts.common import Globals, Thread
from web.wsgiserver import CherryPyWSGIServer
p1=os.path.abspath(os.path.dirname(sys.argv[0]))
CherryPyWSGIServer.ssl_certificate = "/opt/glustermg/ssl/server.crt"
CherryPyWSGIServer.ssl_private_key = "/opt/glustermg/ssl/server.key"


if __name__=='__main__':    
    (status, message) = commands.getstatusoutput('/usr/bin/memcached -d -m 64 -p 12333 -u root -l 127.0.0.1')    
    if status !=0:
        print "memcache start failure!"
    else:
        server_details = Thread.ServerDetailsThread(30)
        cluster_details = Thread.ClusterDetailsThread(30)
        task_details = Thread.TaskDetailsThread(30)
        volume_details = Thread.VolumeDetailsThread(30)
        volume_info = Thread.VolumeInfoThread(30)

	server_details.start()
        cluster_details.start()
        task_details.start()
        volume_details.start()
        volume_info.start()

        try:
            VERSION = Globals.db.select("version")[0].version
        except Exception, e:
            print "Error when get version: " + str(e)
        urls = (
	    '/glustermg/'+VERSION+'/clusters/(.+)/volumes/(.+)/bricks','brickResource.Brick',
            '/glustermg/'+VERSION+'/clusters/(.+)/servers/(.+)/disks/(.+)','serverResource.Disk',
            '/glustermg/'+VERSION+'/clusters/(.+)/servers/(.+)/neofsMount','serverResource.Operation',
	    '/glustermg/'+VERSION+'/clusters/(.+)/servers','serverResource.Servers',
            '/glustermg/'+VERSION+'/clusters/(.+)/servers/(.+)','serverResource.Server',
            '/glustermg/'+VERSION+'/clusters/(.+)/volumes/(.+)/options','volumeResource.Options',
            '/glustermg/'+VERSION+'/clusters/(.+)/volumes/(.+)/logs/download','volumeResource.Download',
            '/glustermg/'+VERSION+'/clusters/(.+)/volumes/(.+)/logs','volumeResource.Logs',    
            '/glustermg/'+VERSION+'/clusters/(.+)/volumes','volumeResource.VolumesService',
            '/glustermg/'+VERSION+'/clusters/(.+)/volumes/(.+)','volumeResource.VolumeService',
            '/glustermg/'+VERSION+'/clusters/(.+)/tasks/(.+)','taskResource.Task',
            '/glustermg/'+VERSION+'/clusters/(.+)/tasks','taskResource.Tasks',
            '/glustermg/'+VERSION+'/clusters','clusterResource.Clusters',
            '/glustermg/'+VERSION+'/clusters/(.+)','clusterResource.Cluster',
            '/glustermg/'+VERSION+'/users','userResource.Users',
            '/glustermg/'+VERSION+'/cifsusers','userResource.CifsUser',
        )    
        app = web.application(urls,globals())
        app.run()
        server_details.stop()
        cluster_details.stop()
        task_details.stop()
        volume_details.stop()
        volume_info.stop()
