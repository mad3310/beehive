'''
Created on 2015-2-5

@author: asus
'''

from componentProxy.abstractContainerModelCreator import AbstractContainerModelCreator
from container.container_model import Container_Model
from utils import _get_gateway_from_ip

class GbalancerclusterContainerModelCreator(AbstractContainerModelCreator):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
    def create(self, args):
    
        component_container_cluster_config = args.get('component_config')
        containerClusterName = args.get('containerClusterName')
        network_mode = args.get('networkMode')
        container_ip_list = args.get('ip_port_resource_list')
        host_ip_list = args.get('host_ip_list')
        component_type = args.get('componentType')
        containerCount = component_container_cluster_config.nodeCount
        create_container_arg_list = []
        mount_dir = component_container_cluster_config.mount_dir
        volumes, binds = self.__inspect_volumes_args(mount_dir)
        for i in range(int(containerCount)):
            container_model = Container_Model()
            container_model.container_cluster_name = containerClusterName
            container_model.container_ip = container_ip_list[i]
            container_model.host_ip = host_ip_list[i]
            container_name = 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1))
            container_model.container_name = container_name
            container_model.network_mode = network_mode
            container_model.volumes = volumes
            container_model.binds = binds
            container_model.lxc_conf = component_container_cluster_config.lxc_conf
            container_model.component_type = component_type
            container_model.image = component_container_cluster_config.image
            container_model.mem_limit = component_container_cluster_config.mem_limit
            gateway = _get_gateway_from_ip(container_ip_list[0])
            
            env = {}
            env.setdefault('NETMASK', '255.255.0.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', container_ip_list[i])
            
            container_model.env = env
            create_container_arg_list.append(container_model)
        
        return create_container_arg_list

    def __inspect_volumes_args(self, mount_dir):
        volumes, binds = {}, {}
        for _dir in mount_dir:
            ro = _dir.pop('ro')
            for k,v in _dir.items():
                volumes.setdefault(k, v)
                binds.setdefault(v, {'bind': k, 'ro' : ro})
        return volumes, binds
