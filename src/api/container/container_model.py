'''
Created on 2015-2-5

@author: asus
'''


class Container_Model(object):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        
        
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
        _binds_binds = binds
        
    @property
    def env(self):
        return self._env
    
    @env.setter
    def env(self, env):
        self._env = env

    @property
    def image(self):
        return self._image
    
    @env.setter
    def image(self, image):
        self._image = image

    @property
    def ports(self):
        return self._ports
    
    @env.setter
    def ports(self, ports):
        self._ports = ports

    @property
    def mem_limit(self):
        return self._mem_limit
    
    @env.setter
    def mem_limit(self, mem_limit):
        self._mem_limit = mem_limit
        
    @property
    def mount_dir(self):
        return self._mount_dir
    
    @env.setter
    def mount_dir(self, mount_dir):
        self._mount_dir = mount_dir
    

        