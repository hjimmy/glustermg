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
import org.gluster.storage.management.client.GlusterServersClient;
import org.gluster.storage.management.client.UsersClient;
import org.gluster.storage.management.core.model.GlusterServer;
import org.gluster.storage.management.core.exceptions.GlusterRuntimeException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.Ignore;

public class GlusterServersSystemTest {
	private GlusterServersClient glusterServersClient;
	private UsersClient usersClient;
	private ClustersClient clustersClient;

	public boolean ServerIsExists(String ServerName) {
		List<GlusterServer> servers = glusterServersClient.getServers();
		for( int i = 0; i < servers.size(); i++ ) {
			if( servers.get(i).getName().equals(ServerName)) {
				return true;
			}
		}
		return false;
	}
	
	@Before
	public void setUp() throws Exception {
		usersClient = new UsersClient();
		usersClient.authenticate(Testbed.USER_NAME, Testbed.PASSWORD);
		String token = usersClient.getSecurityToken();
		clustersClient = new ClustersClient(token);
		clustersClient.registerCluster(Testbed.CLUSTER_NAME, Testbed.SERVER_01);
		glusterServersClient = new GlusterServersClient(token, Testbed.CLUSTER_NAME);
	}

	@After
	public void tearDown() throws Exception {
		clustersClient.deleteCluster(Testbed.CLUSTER_NAME);
	}

	@Test
	public void testGetResourcePath() {
		assertEquals(glusterServersClient.getResourcePath(),"/clusters/" + Testbed.CLUSTER_NAME + "/servers");
	}
	
	@Test
	public void testGetGlusterServerName() {
		assertEquals(glusterServersClient.getGlusterServer(Testbed.SERVER_01).getName(), Testbed.SERVER_01);
	}

	@Test
	public void testGetGlusterServerDiskNum() {
		assertEquals(glusterServersClient.getGlusterServer(Testbed.SERVER_01).getNumOfDisks(), 1);
	}

	
	@Test
	public void testCRUD() {
		try {
			glusterServersClient.addServer(Testbed.SERVER_02);
			assertTrue("addServer failed", ServerIsExists(Testbed.SERVER_02));

			glusterServersClient.removeServer(Testbed.SERVER_02);
			assertFalse("removeServer02 failed", ServerIsExists(Testbed.SERVER_02));

			glusterServersClient.removeServer(Testbed.SERVER_01);
			assertFalse("removeServer01 failed", ServerIsExists(Testbed.SERVER_01));

		} catch (GlusterRuntimeException re) {
			throw new RuntimeException(Testbed.getExceptionInfo(re));
		}
	}
	
	@Ignore
	public void testGetCpuStats() {
		assertNotNull("Get Cpu Stats",glusterServersClient.getCpuStats(Testbed.SERVER_01,"1d"));  // period ???
	}

	@Ignore
	public void testGetMemoryStats() {
		assertNotNull("Get Memory Stats",glusterServersClient.getMemoryStats(Testbed.SERVER_01, "1d"));
	}

	@Ignore
	public void testGetNetworkStats() {
		assertNotNull("Get Network Stats",glusterServersClient.getNetworkStats(Testbed.SERVER_01, "eth0", "1d"));
	}

	@Ignore
	public void testGetAggregatedCpuStats() {
		assertNotNull("Get Aggregated Cpu Stats",glusterServersClient.getAggregatedCpuStats("1d"));
	}

	@Ignore
	public void testGetAggregatedNetworkStats() {
		assertNotNull("Get Aggregated Network Stats",glusterServersClient.getAggregatedNetworkStats("1d"));
	}

}
