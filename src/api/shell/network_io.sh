CID=$1
TASKS=/cgroup/devices/lxc/$CID*/tasks
#PID=$(head -n 1 $TASKS)

for PID in `cat $TASKS`
do
    mkdir -p /var/run/netns
    ln -sf /proc/$PID/ns/net /var/run/netns/$CID
    ip netns exec $CID netstat -i
done