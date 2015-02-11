'''
Created on 2015-2-5

@author: asus
'''
import logging

from componentProxy.abstractContainerModelCreator import AbstractContainerModelCreator
from container.container_model import Container_Model
from utils import _get_gateway_from_ip

class GbalancerContainerModelCreator(AbstractContainerModelCreator):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
    
    def create(self, arg_dict, containerCount, containerClusterName, container_ip_list, component_container_cluster_config):
        component_type = arg_dict.get('componentType')
        network_mode = arg_dict.get('network_mode')
        create_container_arg_list = []
        
        for i in range(int(containerCount)):
            env = {}
            container_model = Container_Model()
            container_model.container_cluster_name = containerClusterName
            container_model.container_ip = container_ip_list[i]
            container_name = 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1))
            container_model.container_name = container_name
            container_model.component_type = 'mclustervip'
            container_model.image = component_container_cluster_config.image
            container_model.mem_limit = component_container_cluster_config.mem_limit
            
            gateway = _get_gateway_from_ip(container_ip_list[0])
            env.setdefault('NETMASK', '255.255.0.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', container_ip_list[i])
            
            container_model.env = env
            create_container_arg_list.append(container_model)
        
        return create_container_arg_list  