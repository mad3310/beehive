'''
Created on 2015-2-5

@author: asus
'''

import re

from tornado.options import options
from utils import get_containerClusterName_from_containerName


class Container_Model(object):
    '''
    classdocs
    '''


    def __init__(self, inspect={}):
        '''
        Constructor
        '''
        
        self.inspect = inspect

    @property
    def component_type(self):
        return self._component_type

    @component_type.setter
    def component_type(self, component_type):
        self._component_type = component_type

    @property
    def container_cluster_name(self):
        return self._container_cluster_name

    @container_cluster_name.setter
    def container_cluster_name(self, container_cluster_name):
        self._container_cluster_name = container_cluster_name

    @property
    def container_ip(self):
        return self._container_ip

    @container_ip.setter
    def container_ip(self, container_ip):
        self._container_ip = container_ip

    @property
    def container_port(self):
        return self._container_port

    @container_port.setter
    def container_port(self, container_port):
        self._container_port = container_port

    @property
    def host_port(self):
        return self._host_port

    @host_port.setter
    def host_port(self, host_port):
        self._host_port = host_port

    @property
    def host_ip(self):
        return self._host_ip

    @host_ip.setter
    def host_ip(self, host_ip):
        self._host_ip = host_ip

    @property
    def container_name(self):
        return self._container_name

    @container_name.setter
    def container_name(self, container_name):
        self._container_name = container_name

    @property
    def volumes(self):
        return self._volumes

    @volumes.setter
    def volumes(self, volumes):
        self._volumes = volumes

    @property
    def binds(self):
        return self._binds

    @binds.setter
    def binds(self, binds):
        self._binds = binds

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, env):
        self._env = env

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def ports(self):
        return self._ports

    @ports.setter
    def ports(self, ports):
        self._ports = ports

    @property
    def mem_limit(self):
        return self._mem_limit

    @mem_limit.setter
    def mem_limit(self, mem_limit):
        self._mem_limit = mem_limit

    @property
    def network_mode(self):
        return self._network_mode

    @network_mode.setter
    def network_mode(self, network_mode):
        self._network_mode = network_mode

    @property
    def port_bindings(self):
        return self._port_bindings

    @port_bindings.setter
    def port_bindings(self, port_bindings):
        self._port_bindings = port_bindings

    @property
    def lxc_conf(self):
        return self._lxc_conf

    @lxc_conf.setter
    def lxc_conf(self, lxc_conf):
        self._lxc_conf = lxc_conf

    def memory(self):
        return self.inspect.get('Config').get('Memory')

    def inspect_volumes(self):
        return self.inspect.get('Volumes')

    def volumes_permissions(self):
        return self.inspect.get('HostConfig').get('Binds')

    def cluster(self, container_name):
        return get_containerClusterName_from_containerName(container_name)

    def zookeeper_id(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if 'ZKID' in item:
                return self.__get_value(item)

    """
        ip supplied when container created
    """
    def ip(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('IP'):
                return self.__get_value(item)

    """
        ip default when container created
    """
    def default_container_ip(self):
        return self.inspect.get('NetworkSettings').get('IPAddress')
        
    def gateway(self):
        
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('GATEWAY'):
                return self.__get_value(item)

    def netmask(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('NETMASK'):
                return self.__get_value(item)

    def __get_value(self, item):
        return re.findall('.*=(.*)', item)[0]

    def inspect_image(self):
        return self.inspect.get('Config').get('Image')

    def name(self):
        name = self.inspect.get('Name')
        if name:
            return name.replace('/', '')

    def hostname(self):
        return self.inspect.get('Config').get('Hostname')

    def id(self):
        return self.inspect.get('Id')
    
    def inspect_port_bindings(self):
        '''
            get the format webportal need
        '''
        
        result = []
        _port_bindings = self.inspect.get('HostConfig').get('PortBindings')
        for con_port_protocol, host_port_ip in _port_bindings.items():
            if host_port_ip:
                _info = {}
                port, protocol = con_port_protocol.split('/')
                _info.setdefault('type', 'user')
                if port == str(options.port):
                    _info.update({'type': 'manager'})
                host_port = host_port_ip[0].get('HostPort')
                _info.setdefault('containerPort', port)
                _info.setdefault('protocol', protocol)
                _info.setdefault('hostPort', host_port)
                
                result.append(_info)
        return result



    def create_info(self, container_node_value):
        create_info = {}
        if isinstance(container_node_value, dict):
            self.inspect = container_node_value.get('inspect')
            isUseIp = container_node_value.get('isUseIp')
            create_info.setdefault('hostIp', container_node_value.get('hostIp') )
            create_info.setdefault('type', container_node_value.get('type') )
            container_name = self.name()
            create_info.setdefault('containerClusterName', self.cluster(container_name) )
            create_info.setdefault('zookeeperId', self.zookeeper_id() )
            create_info.setdefault('gateAddr', self.gateway() )
            create_info.setdefault('netMask', self.netmask() )
            create_info.setdefault('mountDir', str(self.inspect_volumes()) )
            create_info.setdefault('containerName', self.name() )
            if isUseIp:
                create_info.setdefault('ipAddr', self.ip() )
            else:
                create_info.setdefault('port_bindings', self.inspect_port_bindings())
                create_info.setdefault('ipAddr', self.default_container_ip())
        return create_info

    def use_ip(self):
        is_use_ip = False
        _ip = self.ip()
        if _ip:
            is_use_ip = True
        return is_use_ip

    def inspect_component_type(self):
        type_list = ['nginx', 'jetty', 'mcluster', 'gbalancer', 'gbalancerCluster', 'cbase']
        _image = self.inspect_image()
        for _type in type_list:
            if _type in _image:
                return _type
        return 'unknow_type'