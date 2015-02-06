'''
Created on 2015-2-5

@author: asus
'''

class Container_Model(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
        
    @property
    def component_type(self):
        return self._component_type
    
    @component_type.setter
    def component_type(self, component_type):
        _component_type = component_type
        
    @property
    def container_cluster_name(self):
        return self._container_cluster_name
    
    @container_cluster_name.setter
    def container_cluster_name(self, container_cluster_name):
        _container_cluster_name = container_cluster_name
        
    @property
    def container_ip(self):
        return self._container_ip
    
    @container_ip.setter
    def container_ip(self, container_ip):
        _container_ip = container_ip
        
    @property
    def container_port(self):
        return self._container_port
    
    @container_port.setter
    def container_port(self, container_port):
        _container_port = container_port
        
    @property
    def host_port(self):
        return self._host_port
    
    @host_port.setter
    def host_port(self, host_port):
        _host_port = host_port
        
    @property
    def host_ip(self):
        return self._host_ip
    
    @host_ip.setter
    def host_ip(self, host_ip):
        _host_ip = host_ip
        
    @property
    def container_name(self):
        return self._container_name
    
    @container_name.setter
    def container_name(self, container_name):
        _container_name = container_name
        
    @property
    def volumes(self):
        return self._volumes
    
    @volumes.setter
    def volumes(self, volumes):
        _volumes = volumes
        
    @property
    def binds(self):
        return self._binds
    
    @binds.setter
    def binds(self, binds):
        _volumes = binds
        
    @property
    def env(self):
        return self._env
    
    @env.setter
    def env(self, env):
        _env = env
        
        
        
        
        
        
        
        
        
        
        
        
        