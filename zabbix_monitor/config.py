import os
from kazoo.client import KazooClient

rootPath = r"/mad3310/docker"

zk = KazooClient('127.0.0.1:2181')
zk.start()

##================================================================================

def get_cluster_uuid():
    dataNodeName = zk.get_children(rootPath)
    return dataNodeName[0]

def return_children_to_list(path):
    print path
    children = zk.get_children(path)
    
    children_to_list = []
    if len(children) != 0:
        for i in range(len(children)):
            children_to_list.append(children[i])
    return children_to_list

def retrieve_cluster_list():
    clusterUUID = get_cluster_uuid()
    path = "/mad3310/docker/" + clusterUUID + "/container/cluster/"
    return return_children_to_list(path)

def retrieve_container_list(cluster):
    clusterUUID = get_cluster_uuid()
    path = rootPath + "/" + clusterUUID + "/container/cluster/" + cluster
    return return_children_to_list(path)


def get_ports_from_portPool(host_ip):
    clusterUUID = get_cluster_uuid()
    path = rootPath + '/' + clusterUUID + "/portPool/" + host_ip
    return return_children_to_list(path)

##================================================================================


def get_value(path):
    data,_ = zk.get(path)
    
    resultValue = {}
    if data != None and data != '':
        resultValue = eval(data)
    return resultValue

def set_value(path, value):
    print 'write in : %s' % path
    zk.set(path, str(value))

##================================================================================



def add_container_cluster_node():
    clusterUUID = get_cluster_uuid()
    path = rootPath + "/" + clusterUUID + "/container/cluster"
    zk.ensure_path(path)

def config_server_thredhold_to_zk():
    clusterUUID = get_cluster_uuid()
    path = rootPath + "/" + clusterUUID + "/monitor/server"
    zk.ensure_path(path)
    disk_thredhold = {
        'memory_threshold': 10*1024*1024*1024,
        'disk_threshold':{
            'read':10*1024*1024,
            'write':10*1024*1024
        }
    }
    set_value(path, disk_thredhold)


if __name__ == '__main__':
    add_container_cluster_node()
    config_server_thredhold_to_zk()
