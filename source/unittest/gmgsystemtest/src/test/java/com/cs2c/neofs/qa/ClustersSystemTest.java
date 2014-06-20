 /*
  * * Copyright (c) 2012-2012 Gluster, Inc. <http://cs2c.com.cn>
  *
  * This file is part of Junit test of Gluster Management Console .
  *
*/
package com.cs2c.neofs.qa;

import static org.junit.Assert.*;
import java.util.List;
import org.gluster.storage.management.client.ClustersClient;
import org.gluster.storage.management.client.UsersClient;
import org.gluster.storage.management.core.exceptions.GlusterRuntimeException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class ClustersSystemTest {

	private ClustersClient clustersClient;
	private UsersClient usersClient;

	@Before
	public void setUp() throws Exception {
		usersClient = new UsersClient();
		usersClient.authenticate(Testbed.USER_NAME, Testbed.PASSWORD);
		String token = usersClient.getSecurityToken();
		clustersClient = new ClustersClient(token);
	}

	@After
	public void tearDown() throws Exception {

	}

	@Test
	public void testCRUD() {
		try {
			clustersClient.createCluster(Testbed.CLUSTER_NAME);
			List<String> clusters = clustersClient.getClusterNames();
			assertTrue("createCluster Failed", clusters.contains(Testbed.CLUSTER_NAME));

			clustersClient.deleteCluster(Testbed.CLUSTER_NAME);
			clusters = clustersClient.getClusterNames();
			assertFalse("deleteCluster Failed", clusters.contains(Testbed.CLUSTER_NAME));
		}
		catch(GlusterRuntimeException re)
		{
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}

	@Test
	public void testRegisterCluster() {
		try {
			clustersClient.registerCluster(Testbed.CLUSTER_NAME, Testbed.SERVER_01);
			List<String> clusters = clustersClient.getClusterNames();
			assertTrue("registerCluster Failed", clusters.contains(Testbed.CLUSTER_NAME));

			clustersClient.deleteCluster(Testbed.CLUSTER_NAME);
		} catch (GlusterRuntimeException re) {
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}

	@Test
	public void testGetResourcePath() {
		assertEquals(clustersClient.getResourcePath(),"/clusters");
	}

	@Test
	public void testGetClusterNames() {
        List<String> clusters = clustersClient.getClusterNames();
        for (int i = 0; i < clusters.size(); i++) {
            System.out.println(clusters.get(i));
         }
	}
}
