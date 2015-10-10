glustermg
=========

Glustermg(Gluster Managerment Gateway) provides simple and powerful REST APIS for managing gluster storage cluster

Prerequsites
=============

For this to work python

* Version 2.6

* Should be running on ns6.x or RHEl6.x or centos6.x

* Glusterfs show be verion 3.4 or 3.5 


Installation
==========
  Install the latest version of  with the following command...

  # yum install mysql mysql-server memcached python-memcached python-webpy glusterfs glusterfs-server

  # git clone https://github.com/hjimmy/glustermg.git
  
  # cd glustermg 
  
  # sh build.sh
  
  # rpmbuild -ba glustermg.spec
 
  # rpm -ivh /root/rpmbuild/RPMS/x86_64/glustermg-*
  
  # mysq -u root -p{$pwd}
    mysql> create database webpy;

    mysql> GRANT ALL PRIVILEGES ON *.* TO 'gluster'@'localhost' IDENTIFIED BY 'neokylin123' WITH GRANT OPTION;
  
    mysql> GRANT ALL PRIVILEGES ON *.* TO 'gluster'@'%' IDENTIFIED BY 'neokylin123' WITH GRANT OPTION;
   
    mysql> flush privileges;

  # sh /opt/glustermg/2.4/glustermg/scripts/gateway/sql/webpy_table.sh

Test
===========
 curl --request GET --user neoadmin:neokylin123 https://10.1.110.86:8445/glustermg/1.0.0alpha/clusters --insecure 
 
For more info,read Gluster_Management_Gateway-1.0.0alpha-REST_API_Guide-en-US.pdf 


