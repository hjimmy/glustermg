 /*
  * * Copyright (c) 2012-2012 Gluster, Inc. <http://cs2c.com.cn>
  *
  * This file is part of Junit test of Gluster Management Console .
  *
*/
package com.cs2c.neofs.qa;

import static org.junit.Assert.*;

import java.util.List;

import org.gluster.storage.management.client.UsersClient;
import org.gluster.storage.management.client.ClustersClient;
import org.gluster.storage.management.client.GlusterServersClient;
import org.gluster.storage.management.client.NeofsClient;
import org.gluster.storage.management.core.exceptions.GlusterRuntimeException;
import org.gluster.storage.management.core.model.Brick;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.Ignore;

public class NeofsSystemTest {

	private UsersClient usersClient;
    private ClustersClient  clustersClient;
    private GlusterServersClient glusterServersClient;
	private NeofsClient neofsClient;

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

		neofsClient = new NeofsClient(token, Testbed.CLUSTER_NAME);
	}

	@After
	public void tearDown() throws Exception {
		try {
			glusterServersClient.removeServer(Testbed.SERVER_01);
			glusterServersClient.removeServer(Testbed.SERVER_02);
			clustersClient.deleteCluster(Testbed.CLUSTER_NAME);
		} catch (GlusterRuntimeException re) {
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}

	@Test
	public void test() {
		try {
			List<Brick> brickList = clustersClient.getNeofsMountPoints(Testbed.CLUSTER_NAME);
			neofsClient.setupVolume(brickList);

			neofsClient.mount(Testbed.SERVER_01);
			assertTrue(neofsClient.checkMount(Testbed.SERVER_01));

			neofsClient.umount(Testbed.SERVER_01);
			assertFalse(neofsClient.checkMount(Testbed.SERVER_01));

			neofsClient.teardownVolume();
		} catch (GlusterRuntimeException re) {
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}
}
