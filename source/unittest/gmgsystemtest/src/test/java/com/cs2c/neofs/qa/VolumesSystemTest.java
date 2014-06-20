 /*
  * * Copyright (c) 2012-2012 Gluster, Inc. <http://cs2c.com.cn>
  *
  * This file is part of Junit test of Gluster Management Console .
  *
*/
package com.cs2c.neofs.qa;

import static org.junit.Assert.*;

import java.io.InputStreamReader;
import java.io.LineNumberReader;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.gluster.storage.management.client.UsersClient;
import org.gluster.storage.management.client.ClustersClient;
import org.gluster.storage.management.client.VolumesClient;
import org.gluster.storage.management.client.GlusterServersClient;
import org.gluster.storage.management.core.model.Brick;
import org.gluster.storage.management.core.model.User;
import org.gluster.storage.management.core.model.Volume;
import org.gluster.storage.management.core.model.VolumeCIFSUsers;
import org.gluster.storage.management.core.model.VolumeLogMessage;
import org.gluster.storage.management.core.model.Brick.BRICK_STATUS;
import org.gluster.storage.management.core.model.Volume.TRANSPORT_TYPE;
import org.gluster.storage.management.core.model.Volume.VOLUME_TYPE;
import org.gluster.storage.management.core.utils.GlusterCoreUtil;
import org.gluster.storage.management.core.exceptions.GlusterRuntimeException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class VolumesSystemTest {

	private UsersClient usersClient;
	private ClustersClient clustersClient;
	private VolumesClient volumesClient;
	private GlusterServersClient glusterServersClient;

	@Before
	public void setUp() throws Exception {
        usersClient = new UsersClient();
		usersClient.authenticate(Testbed.USER_NAME, Testbed.PASSWORD);
		String token = usersClient.getSecurityToken();

		clustersClient = new ClustersClient(token);
		clustersClient.createCluster(Testbed.CLUSTER_NAME);

		glusterServersClient = new GlusterServersClient(token, Testbed.CLUSTER_NAME);
		glusterServersClient.addServer(Testbed.SERVER_01);
		glusterServersClient.addServer(Testbed.SERVER_02);

		volumesClient = new VolumesClient(token, Testbed.CLUSTER_NAME);
	}

	@After
	public void tearDown() throws Exception {
		glusterServersClient.removeServer(Testbed.SERVER_01);
		glusterServersClient.removeServer(Testbed.SERVER_02);
		clustersClient.deleteCluster(Testbed.CLUSTER_NAME);
	}

	@Test
	public void testVolume() {
		try {
		Volume volume = new Volume();

		volume.setName(Testbed.VOLUME_NAME);
		volume.setVolumeType(VOLUME_TYPE.DISTRIBUTE);
		volume.setTransportType(TRANSPORT_TYPE.ETHERNET);
		volume.setOption("", "");

		Brick brick1 = new Brick(Testbed.SERVER_01, BRICK_STATUS.ONLINE, Testbed.BRICK_PATH);
		Brick brick2 = new Brick(Testbed.SERVER_02, BRICK_STATUS.ONLINE, Testbed.BRICK_PATH);
		volume.addBrick(brick1);

		volumesClient.createVolume(volume);
		assertTrue(volumesClient.volumeExists(Testbed.VOLUME_NAME));

		//Volume Options
		volumesClient.setVolumeOption(Testbed.VOLUME_NAME,"cluster.self-heal-window-size", "32");
		assertEquals(volumesClient.getVolume(Testbed.VOLUME_NAME).getOptions().get("cluster.self-heal-window-size"),"32");
		volumesClient.resetVolumeOptions(Testbed.VOLUME_NAME);
		assertEquals(volumesClient.getVolume(Testbed.VOLUME_NAME).getOptions().get("cluster.self-heal-window-size"), null);

		volumesClient.startVolume(Testbed.VOLUME_NAME, false);
		assertEquals(volumesClient.getVolume(Testbed.VOLUME_NAME).getStatus().toString(),"ONLINE");

		assertEquals(volumesClient.getVolume(Testbed.VOLUME_NAME).toString(), Testbed.VOLUME_NAME);
		assertNotNull(volumesClient.getAllVolumes());

		List<Brick> brickList =  new ArrayList<Brick>();
		brickList.add(brick2);
		volumesClient.addBricks(Testbed.VOLUME_NAME, brickList);
		assertEquals(2,volumesClient.getVolume(Testbed.VOLUME_NAME).getBricks().size());

		volumesClient.removeBricks(Testbed.VOLUME_NAME, brickList, true);//MUST be true, in order to delete brick dirs
		assertEquals(1,volumesClient.getVolume(Testbed.VOLUME_NAME).getBricks().size());

		volumesClient.stopVolume(Testbed.VOLUME_NAME, false);
		assertEquals(volumesClient.getVolume(Testbed.VOLUME_NAME).getStatus().toString(),"OFFLINE");

		volumesClient.deleteVolume(Testbed.VOLUME_NAME, true);//MUST be true, in order to delete brick dirs
		assertFalse(volumesClient.volumeExists(Testbed.VOLUME_NAME));
		} catch (GlusterRuntimeException re) {
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}
}
