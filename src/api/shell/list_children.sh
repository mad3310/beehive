#!/bin/sh

list_d ()
{
    local children=$(ps -o pid= --ppid "$1")
    if [[ ! -z $children ]];
    then
        for pid in $children
        do
            echo "$pid"
            #childrens[${#childrens[@]}]="$pid"
            list_d $pid
        done
    fi
    #echo children"$children\n"
}

#childrens=()
list_d $1
#echo ${childrens[*]}
