 /*
  * * Copyright (c) 2012-2012 Gluster, Inc. <http://cs2c.com.cn>
  *
  * This file is part of Junit test of Gluster Management Console .
  * junli.li@cs2c.com.cn  2012-04-24
*/
package com.cs2c.neofs.qa;

import static org.junit.Assert.*;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.util.List;

import org.gluster.storage.management.client.UsersClient;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

public class UsersSystemTest {
	private UsersClient usersClient;

	@BeforeClass
	public static void setUpBeforeClass() throws Exception {
	}

	@AfterClass
	public static void tearDownAfterClass() throws Exception {
	}

	@Before
	public void setUp() throws Exception {
		usersClient = new UsersClient();
		usersClient.authenticate(Testbed.USER_NAME, Testbed.PASSWORD);
	}

	@After
	public void tearDown() throws Exception {
	}

	public boolean CifsUserIsExists(String UserName) {
		List<String> users = usersClient.listCIFSUsers();
	     for (int j = 0; j < users.size(); j++) {
	        	if(users.get(j).equals(UserName)) {
	        		return true;
	        	}
	     }
	     return false;
	}
	
	@Test
	public void testGetResourcePath() 
		throws Exception {
		assertEquals(usersClient.getResourcePath(),"/cifsusers");
	}
	
	@Test
	public void testAddUserCifs() {
		usersClient.addUserCifs("cifsuser1", "qwe123");
		usersClient.addUserCifs("cifsuser2", "qwe123");
		usersClient.addUserCifs("tmpuser", "qwe123");
		assertTrue("Add Cifsuser cifsuser1 successfully",CifsUserIsExists("cifsuser1"));
		assertTrue("Add Cifsuser cifsuser2 successfully",CifsUserIsExists("cifsuser2"));
		assertTrue("Add Cifsuser tmpuser successfully",CifsUserIsExists("tmpuser"));
		assertFalse("junittest-user not exists",CifsUserIsExists("junittest-user"));
	}
	
	@Test
	public void testListCIFSUsers() {
		 List<String> users = usersClient.listCIFSUsers();
	     for (int j = 0; j < users.size(); j++) {
	        	System.out.println(users.get(j));
	     }
	     assertNotNull("Get CIFSUsers",users);
	}

	@Test
	public void testChangePasswordOfUserCifs() {
		usersClient.changePasswordOfUserCifs("cifsuser1", "neokylin123");
		usersClient.changePasswordOfUserCifs("cifsuser2", "neokylin123");
	}

	@Test
	public void testDeluserCifs() throws Exception {
		 usersClient.delUserCifs("cifsuser1");
		 usersClient.delUserCifs("cifsuser2");
		 usersClient.delUserCifs("tmpuser");
		 assertFalse("Delete Cifsuser tmpuser successfully",CifsUserIsExists("cifsuser1"));
		 assertFalse("Delete Cifsuser tmpuser successfully",CifsUserIsExists("cifsuser2"));
		 assertFalse("Delete Cifsuser tmpuser successfully",CifsUserIsExists("tmpuser"));
	}
	
	public static void main(String[] args) {
		new org.junit.runner.JUnitCore().run(UsersSystemTest.class);
	}

}
