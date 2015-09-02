'''
Created on 2015-2-5

@author: asus
'''

from container.container_model import Container_Model
from utils import _get_gateway_from_ip
from tornado.options import options


class BaseContainerModelCreator(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        
    def create(self, args):
        
        component_type = args.get('componentType')
        network_mode = args.get('networkMode')
        _component_container_cluster_config = args.get('component_config')
        cluster = args.get('containerClusterName')
        ip_port_resource = args.get('ip_port_resource_list')
        host_ip_list = args.get('host_ip_list')
        added = args.get('added', False)
        
        volumes, binds = {}, {}
        if hasattr(_component_container_cluster_config, 'mount_dir'):
            mount_dir = _component_container_cluster_config.mount_dir
            volumes, binds = self.__get_normal_volumes_args(mount_dir)
        
        create_container_arg_list = []
        containerCount = _component_container_cluster_config.nodeCount
        container_names = _component_container_cluster_config.container_names
        for i in range(int(containerCount)):
            container_model = Container_Model()
            container_model.added = added
            container_model.component_type = component_type
            host_ip = host_ip_list[i]
            container_model.host_ip = host_ip
            container_model.network_mode = network_mode
            container_model.container_cluster_name = cluster
            container_name = container_names[i]
            container_model.container_name = container_name
            container_model.volumes = volumes
            container_model.binds = binds
            container_model.image = _component_container_cluster_config.image
            container_model.lxc_conf = _component_container_cluster_config.lxc_conf
            container_model.mem_limit = _component_container_cluster_config.mem_limit
            
            if 'bridge' == network_mode:
                ports = _component_container_cluster_config.ports
                container_model.ports = ports
                port_list = ip_port_resource.get(host_ip)
                port_list = [('0.0.0.0', item) for item in port_list]
                port_bindings = dict(zip(ports, port_list))
                container_model.port_bindings = port_bindings
            else:
                container_ip = ip_port_resource[i]
                container_model.container_ip = container_ip
                env = {}
                if component_type in ('mcluster','zookeeper'):
                    for j, containerIp in enumerate(ip_port_resource):
                        env.setdefault('N%s_IP' % str(j+1), containerIp)
                        env.setdefault('N%s_HOSTNAME' % str(j+1), container_names[j])
                        env.setdefault('ZKID', i+1)
                        env.setdefault('NODE_COUNT', containerCount)
                        
                gateway = _get_gateway_from_ip(container_ip)
                #env.setdefault('IFACE', options.test_cluster_NIC)
                env.setdefault('NETMASK', '255.255.0.0')
                env.setdefault('GATEWAY', gateway)
                env.setdefault('HOSTNAME', container_name)
                env.setdefault('IP', container_ip)
                container_model.env = env
            
            create_container_arg_list.append(container_model)
            
        return create_container_arg_list
    
    def __get_normal_volumes_args(self, mount_dir, ro=False):
        volumes, binds = {}, {}
        for _dir in mount_dir:
            ro = _dir.pop('ro')
            for k,v in _dir.items():
                volumes.setdefault(k, v)
                if '/srv/mcluster' in k:
                    binds = {}
                else:
                    binds.setdefault(v, {'bind': k, 'ro' : ro})
        return volumes, binds
