package com.cs2c.neofs.qa;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.junit.runners.Suite.SuiteClasses;
import org.junit.BeforeClass;
import org.gluster.storage.management.client.constants.ClientConstants;

@RunWith(Suite.class)
@SuiteClasses({
	ClustersSystemTest.class
//	GlusterServersSystemTest.class,
//	NeofsSystemTest.class,
//	VolumesSystemTest.class,
//	UsersSystemTest.class
	})
public class AllSystemTests {
	@BeforeClass
	public static void setProperty() {
		System.setProperty(ClientConstants.SYS_PROP_SERVER_URL, Testbed.GMG_SERVER_URL);
		System.setProperty(ClientConstants.SYS_PROP_API_VERSION, Testbed.API_VERSION);
	}
	public static void main(String[] args) {
		new org.junit.runner.JUnitCore().run(AllSystemTests.class);
	}
}
