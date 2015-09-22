#!/bin/bash

get_dev_number() {
    mount_dir=$1
    dir_fs=`df -P | grep $mount_dir"$" | awk '{print $1}'`
    dm="/dev/"`ls -l $dir_fs | awk -F"/" '{print $NF}'`
    number=`ls -l $dm | awk '{print $5$6}' | awk -F "," '{print $1":"$2}'`
    echo $number
}

get_dev_number $1