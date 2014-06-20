#!/bin/bash

#echo "--------------------------------------"
#echo "# 5.Setup Neofs Storage  #"
#echo "--------------------------------------"

RCLOCAL_FILE="/etc/rc.d/rc.local"
FSTAB_FILE="/etc/fstab"
NKEV_CONFIG="/etc/nkev.conf"
NKEV_CONFIG_STATUS="/etc/nkev/configuration_status"

VM_DIR="/srv/cloud/neo/var/vms"
IMAGE_DIR="/srv/cloud/neo-images"
VARIMAGE_DIR="/srv/cloud/neo/var/images"

server_ip_for_neofs=$1

mount_neofs_dir()
{
    mount -t glusterfs $1:$2 $3 > /dev/null 2>&1

    # 0: find it
    # 1: not find it
    grep $3 /etc/mtab > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        #echo "mount success!"
        echo -e "$1:$2\t$3\tglusterfs\tdefaults,_netdev\t1 1">>/etc/fstab
    else
        #echo "mount failed!!"
        exit 1
    fi
}

mkdir -p $VM_DIR
mkdir -p $IMAGE_DIR

# add iptables rules
iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 24007:24008 -j ACCEPT
iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 24009:24025 -j ACCEPT

echo "iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 24007:24008 -j ACCEPT" >> $RCLOCAL_FILE
echo "iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 24009:24025 -j ACCEPT" >> $RCLOCAL_FILE

#echo -e "mount neofs storage neofs-vms to $VM_DIR"
mount_neofs_dir $server_ip_for_neofs neofs-vms $VM_DIR

#echo -e "mount neofs storage neofs-images to $IMAGE_DIR"
mount_neofs_dir $server_ip_for_neofs neofs-images $IMAGE_DIR

# Neofs at /etc/fstab may not work, remount it in rc.local
echo "umount $VM_DIR" >> $RCLOCAL_FILE
echo "umount $IMAGE_DIR" >> $RCLOCAL_FILE
echo "mount $VM_DIR" >> $RCLOCAL_FILE
echo "mount $IMAGE_DIR" >> $RCLOCAL_FILE

# write Neofs info to $NKEV_CONFIG
echo "storage_type=neofs" >> $NKEV_CONFIG
echo "share_storage_ip=$server_ip_for_neofs" >> $NKEV_CONFIG

if [ -f $NKEV_CONFIG_STATUS ];then
    sed -i 's/^storage=.*$/storage=1/g' $NKEV_CONFIG_STATUS
fi

# VM_DIR IMAGE_DIR ownership config
# only run on fronted node, use glustermg rpm to determine fronted or not
rpm -q glustermg > /dev/null 2>&1
if [ $? -eq 0 ]
then
        chown neoadmin:cloud $VM_DIR > /dev/null 2>&1
        mkdir $IMAGE_DIR/{os,data,iso} > /dev/null 2>&1
        chown -R neoadmin:cloud $IMAGE_DIR > /dev/null 2>&1

	mkdir -p $VARIMAGE_DIR

        #echo -e "mount neofs storage var-images to $VARIMAGE_DIR"
        mount_neofs_dir $server_ip_for_neofs var-images $VARIMAGE_DIR

        # Neofs at /etc/fstab may not work, remount it in rc.local
        echo "umount $VARIMAGE_DIR" >> $RCLOCAL_FILE
        echo "mount $VARIMAGE_DIR" >> $RCLOCAL_FILE
        chown neoadmin:cloud $VARIMAGE_DIR > /dev/null 2>&1

fi

# HA
service neokylinha status > /dev/null
if [ $? -ne 0 ]; then
    exit 0
fi

fs_vm=`/usr/sbin/crm_resource -l|grep fs-vm`
for fs in $fs_vm
do
    /usr/sbin/crm_resource -r $fs --cleanup > /dev/null  2>&1
done

fs_image=`/usr/sbin/crm_resource -l|grep fs-image`
for fs in $fs_image
do
    /usr/sbin/crm_resource -r $fs --cleanup > /dev/null  2>&1
done

exit 0
