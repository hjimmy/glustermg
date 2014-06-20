#!/bin/bash

RCLOCAL_FILE="/etc/rc.d/rc.local"
FSTAB_FILE="/etc/fstab"
NKEV_CONFIG="/etc/nkev.conf"

VM_DIR="/srv/cloud/neo/var/vms"
IMAGE_DIR="/srv/cloud/neo-images"
VARIMAGE_DIR="/srv/cloud/neo/var/images"


umount_neofs_dir()
{
    umount -fl $1 > /dev/null 2>&1

    # 0: find it 
    # 1: not find it
    grep $1 /etc/mtab > /dev/null 2>&1

    if [ $? -eq 0 ]; then
		# umount failed
        exit 1
    else
		echo
		# umount success
    fi
}

# clear $FSTAB_FILE
sed -i "\~$VM_DIR~d" $FSTAB_FILE
sed -i "\~$IMAGE_DIR~d" $FSTAB_FILE

# clear rc.local
sed -i '/24007:24008/d' $RCLOCAL_FILE
sed -i '/24009:24025/d' $RCLOCAL_FILE

sed -i "\~$VM_DIR~d" $RCLOCAL_FILE
sed -i "\~$IMAGE_DIR~d" $RCLOCAL_FILE

# clear $NKEV_CONFIG
sed -i '/storage_type/d' $NKEV_CONFIG  > /dev/null 2>&1
sed -i '/share_storage_ip/d' $NKEV_CONFIG > /dev/null 2>&1

# umount two dirs
umount_neofs_dir $VM_DIR
umount_neofs_dir $IMAGE_DIR

#only done on front node
rpm -q glustermg > /dev/null 2>&1
if [ $? -eq 0 ];then
    sed -i "\~$VARIMAGE_DIR~d" $FSTAB_FILE
    sed -i "\~$VARIMAGE_DIR~d" $RCLOCAL_FILE
    umount_neofs_dir $VARIMAGE_DIR
fi

if [ -f $NKEV_CONFIG_STATUS ];then
    sed -i 's/^storage=.*$/storage=0/g' $NKEV_CONFIG_STATUS
fi

exit 0
