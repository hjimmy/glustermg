#! /bin/bash

VM_DIR="/srv/cloud/neo/var/vms"
IMAGE_DIR="/srv/cloud/neo-images"
VARIMAGE_DIR="/srv/cloud/neo/var/images"

rpm -q glustermg > /dev/null 2>&1
if [ $? -eq 0 ]; then
     df 2> /dev/null | grep $VM_DIR > /dev/null 2>&1 && df 2> /dev/null | grep $IMAGE_DIR > /dev/null 2>&1 && df 2> /dev/null | grep $VARIMAGE_DIR > /dev/null 2>&1
     ret=$?
else
     df 2> /dev/null | grep $VM_DIR > /dev/null 2>&1 && df 2> /dev/null | grep $IMAGE_DIR > /dev/null 2>&1
     ret=$?
fi

if [ $ret -ne 0 ]; then
    echo "false"
else
    echo "true"
fi
