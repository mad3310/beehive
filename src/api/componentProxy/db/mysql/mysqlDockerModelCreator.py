'''
Created on 2015-2-1

@author: asus
'''

from componentProxy.abstractDockerModelCreator import AbstractContainerModelCreator
from docker_letv.docker_model import Docker_Model


class MysqlDockerModelCreator(AbstractContainerModelCreator):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

    def create(self, arg_dict):
        
        _container_name = arg_dict.get('container_name')
        _containerClusterName = arg_dict.get('container_cluster_name')
        _env = eval( arg_dict.get('env') )
        _image = arg_dict.get('image')
        _mem_limit = int(arg_dict.get('mem_limit'))
        _volumes = eval( arg_dict.get('volumes') )
        _binds = eval( arg_dict.get('binds') )
        _ports = eval( arg_dict.get('ports'))
        _network_mode = arg_dict.get('network_mode')
        _host_ip = arg_dict.get('host_ip')
        _component_type = arg_dict.get('component_type')
        
        _docker_model = Docker_Model()
        _docker_model.image = _image
        _docker_model.mem_limit = _mem_limit
        _docker_model.volumes = _volumes
        _docker_model.binds = _binds
        _docker_model.privileged = True
        _docker_model.network_mode = 'bridge'
        _docker_model.name = _container_name
        _docker_model.environment = _env
        _docker_model.hostname = _container_name
        _docker_model.ports = _ports
        _docker_model.host_ip = _host_ip
        _docker_model.component_type = _component_type
        if 'ip' == _network_mode:
            _docker_model.use_ip = True
        else:
            _docker_model.use_ip = False
        
        return _docker_model

        