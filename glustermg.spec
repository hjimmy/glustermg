%define product_family Gluster Management Gateway
%define release_version 2.4
%define source glustermg-%{release_version}.x86_64.tar.gz
%define current_arch %{_arch}
%ifarch i386
%define current_arch x86_64
%endif

Summary:        %{product_family} Management Gateway
Name:           glustermg
Version:        %{release_version}
Release:        1
License:        GPLv3+
Group:          System Environment/Base
Source0:        %{source}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires:       openssl memcached python-memcached
Requires:       samba >= 3.5.6
Requires:       python >= 2.4.3
Requires:       openssh

%description
%{product_family} Management Gateway

%package        backend
Summary:        %{product_family} server side backend tools
Group:          System Environment/Base
Requires:       python >= 2.4.3
%description    backend
%{product_family} server side backend tools

%prep
tar xvf $RPM_SOURCE_DIR/%{source} -C $RPM_BUILD_DIR/

%build

%install
mkdir -p $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend
mkdir -p $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg/scripts
mkdir -p $RPM_BUILD_ROOT/opt/glustermg/keys
mkdir -p $RPM_BUILD_ROOT/opt/glustermg/etc
mkdir -p $RPM_BUILD_ROOT/etc/init.d/

cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/__init__.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/resource $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/services $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/__init__.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg/scripts
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/common $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg/scripts
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/gateway $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg/scripts

cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/ssl $RPM_BUILD_ROOT/opt/glustermg/

cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/backend $RPM_BUILD_ROOT/opt/glustermg//%{release_version}/
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/common/Globals.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/common/XmlHandler.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/common/Utils.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/
cp -rf $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/scripts/common/VolumeUtils.py $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/
sed -i '/import web/d' $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/Globals.py
sed -i '/import memcache/d' $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/Globals.py
sed -i '/db = web.database/d' $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/Globals.py
sed -i '/mc = memcache.Client/d' $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/backend/Globals.py

cp -fr $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/glustermg $RPM_BUILD_ROOT/etc/init.d/

cp -fr $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}/web $RPM_BUILD_ROOT/opt/glustermg/%{release_version}/glustermg/

%post
if [ -d /usr/lib/python2.6/site-packages/web ];then
   rm -fr /usr/lib/python2.6/site-packages/web.remove
   mv /usr/lib/python2.6/site-packages/web /usr/lib/python2.6/site-packages/web.remove
   mv /opt/glustermg/%{release_version}/glustermg/web /usr/lib/python2.6/site-packages/
else
   mv /opt/glustermg/%{release_version}/glustermg/web /usr/lib/python2.6/site-packages/
fi

if [ ! -f /opt/glustermg/keys/gluster.pem ]; then
   if [ ! -f /root/.ssh/id_rsa.pub ]; then
       ssh-keygen -t rsa -f /root/.ssh/id_rsa -N ''
   fi
   cp -f /root/.ssh/id_rsa $RPM_BUILD_ROOT/opt/glustermg/keys/gluster.pem
   cp -f /root/.ssh/id_rsa.pub  $RPM_BUILD_ROOT/opt/glustermg/keys/gluster.pub
fi

if [ ! -f /opt/glustermg/etc/volumes.cifs ]; then
    touch /opt/glustermg/etc/volumes.cifs
fi
if [ ! -f /opt/glustermg/etc/users.cifs ]; then
    touch /opt/glustermg/etc/users.cifs
fi

grep "/etc/init.d/glustermg start" /etc/rc.local 2>&1>/dev/null
if [ $? != 0 ];then
    echo "/etc/init.d/glustermg start" >> /etc/rc.local
fi

%post backend
python  /opt/glustermg/%{release_version}/backend/setup_cifs_config.py

%preun
sed -i '/\/etc\/init.d\/glustermg start/d' /etc/rc.local

%clean
rm -fr $RPM_BUILD_DIR/glustermg-%{release_version}.%{current_arch}

%files
%defattr(-,root,root)
/opt/glustermg/keys
/opt/glustermg/%{release_version}/glustermg
/etc/init.d/glustermg
/opt/glustermg/ssl/
/opt/glustermg/etc

%files backend
%defattr(-,root,root)
/opt/glustermg/%{release_version}/backend


%changelog
* Mon Sep 16 2013 junli.li - 2.4-1
- change gluster.pem 

