#!/bin/bash

get_iops() {
    mount_dir=$1
    dir_fs=`df -P | grep $mount_dir"$" | awk '{print $1}'`
    dm=`ls -l $dir_fs | awk -F"/" '{print $NF}'`
    iops=`iostat -k | grep -w "$dm" | awk '{print $3,$4}'`
    echo $iops
}

get_iops $1
