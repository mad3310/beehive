'''
Created on 2015-2-5

@author: asus
'''
import logging

from componentProxy.abstractContainerModelCreator import AbstractContainerModelCreator
from container.container_model import Container_Model
from utils import _get_gateway_from_ip

class MySQLContainerModelCreator(AbstractContainerModelCreator):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        
    {'container_cluster_name': 'dh', 'volumes': {'/srv/mcluster': '', '/data/mcluster_data': '/data/mcluster_data'}, 
     'component_type': 'mclusternode', 'image': 'letv/mcluster:0.0.5', 'host_ip': '192.168.33.141', 'network_mode': 'ip', 
     'binds': {'/data/mcluster_data': {'bind': '/data/mcluster_data'}}, 
     'env': {'IP': '192.168.1.101', 'N3_IP': '192.168.1.103', 'HOSTNAME': 'd-mcl-dh-n-1', 'NETMASK': '255.255.0.0', 
             'N2_IP': '192.168.1.102', 'ZKID': 1, 'N3_HOSTNAME': 'd-mcl-dh-n-3', 'N1_IP': '192.168.1.101', 'GATEWAY': '192.168.0.1', 
             'N1_HOSTNAME': 'd-mcl-dh-n-1', 'N2_HOSTNAME': 'd-mcl-dh-n-2'}, 
     'container_name': 'd-mcl-dh-n-1', 'mem_limit': 536870912, 'ports': [2181, 2888, 3306, 3888, 4567, 4568, 4569], 
     'container_ip': '192.168.1.101'}
        
    def create(self, arg_dict, containerCount, containerClusterName, container_ip_list, _component_container_cluster_config):
        
        component_type = arg_dict.get('componentType')
        network_mode = arg_dict.get('network_mode')
        create_container_arg_list = []
        mount_dir = _component_container_cluster_config.mount_dir
        volumes, binds = self.__get_normal_volumes_args(mount_dir)
        for i in range(int(containerCount)):
            env = {}
            container_model = Container_Model()
            container_model.component_type = component_type
            container_model.network_mode = network_mode
            container_model.container_cluster_name = containerClusterName
            container_model.container_ip = container_ip_list[i]
            container_name = 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1))
            container_model.container_name = container_name
            container_model.component_type = 'mclusternode'
            container_model.volumes = volumes
            container_model.binds = binds
            container_model.image = _component_container_cluster_config.image
            container_model.ports = _component_container_cluster_config.ports
            container_model.mem_limit = _component_container_cluster_config.mem_limit
            
            for j, containerIp in enumerate(container_ip_list):
                env.setdefault('N%s_IP' % str(j+1), containerIp)
                env.setdefault('N%s_HOSTNAME' % str(j+1), 'd-mcl-%s-n-%s' % (containerClusterName, str(j+1)))
                
            gateway = _get_gateway_from_ip(containerIp)
            env.setdefault('ZKID', i+1)
            env.setdefault('NETMASK', '255.255.0.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', container_ip_list[i])
            
            container_model.env = env
            create_container_arg_list.append(container_model)
            
        return create_container_arg_list
    
    def __get_normal_volumes_args(self, mount_dir):
        volumes, binds = {}, {}
        for k,v in mount_dir.items():
            volumes.setdefault(k, v)
            if '/srv/mcluster' in k:
                binds = {}
            else:
                binds.setdefault(v, {'bind': k})
        return volumes, binds

