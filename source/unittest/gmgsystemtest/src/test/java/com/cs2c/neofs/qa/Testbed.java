package com.cs2c.neofs.qa;

import org.gluster.storage.management.core.exceptions.GlusterRuntimeException;

public class Testbed {
	public static String GMG_SERVER_URL = "http://10.1.82.206:2223/glustermg/";
	public static String USER_NAME = "gluster";
	public static String PASSWORD = "neokylin123";
	public static String SERVER_GMG = "nkscloudweb-yoyo";
	public static String SERVER_01 = "su02";
	public static String SERVER_02 = "n_su03";
	public static String CLUSTER_NAME = "qa-cluster";
	public static String VOLUME_NAME = "qa-volume";
	public static String CIFS_USER_01 = "qa-cifsuser01";
	public static String CIFS_USER_02 = "qa-cifsuser02";
	public static String BRICK_PATH = "/neofs/qa-brick";
	public static String API_VERSION = "1.0.0";

	public static String getExceptionInfo(GlusterRuntimeException re)
	{
		re.printStackTrace();
		return re.getErrorResponse().getCode()+":"+re.getErrorResponse().getMessage();
	}
}
