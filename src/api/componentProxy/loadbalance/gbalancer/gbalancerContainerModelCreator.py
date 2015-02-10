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


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def create(self, arg_dict, containerCount, containerClusterName):
        _network_mode = arg_dict.get('network_mode')
        if "ip" == _network_mode:
            containerIPList = self.ip_opers.retrieve_ip_resource(containerCount)
            
        create_container_arg_list = []
        '''
        @todo: need volumes and binds?
        '''
        volumes, binds = self.__get_normal_volumes_args()
        for i in range(int(containerCount)):
            env = {}
            container_model = Container_Model()
            container_model.container_cluster_name = containerClusterName
            container_model.container_ip = containerIPList[i]
            container_name = 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1))
            container_model.container_name = container_name
            container_model.component_type = 'mclustervip'
            container_model.volumes = volumes
            container_model.binds = binds
            for j, containerIp in enumerate(containerIPList):
                env.setdefault('N%s_IP' % str(j+1), containerIp)
                env.setdefault('N%s_HOSTNAME' % str(j+1), 'd-mcl-%s-n-%s' % (containerClusterName, str(j+1)))
                env.setdefault('ZKID', i+1)
                
            gateway = _get_gateway_from_ip(containerIp)
            env.setdefault('NETMASK', '255.255.0.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', containerIPList[i])
            
            container_model.env = env
            create_container_arg_list.append(container_model)
        
        return create_container_arg_list
    
    '''
    @todo: gbalancer need to bind volumn?
    '''
    def __get_normal_volumes_args(self):
        volumes, binds = {}, {}
        mcluster_conf_info = self.zkOper.retrieve_mcluster_info_from_config()
        logging.info('mcluster_conf_info: %s' % str(mcluster_conf_info))
        mount_dir = eval( mcluster_conf_info.get('mountDir') )
        for k,v in mount_dir.items():
            volumes.setdefault(k, v)
            if '/srv/mcluster' in k:
                binds = {}
            else:
                binds.setdefault(v, {'bind': k})
        return volumes, binds   