'''
Created on 2015-2-1

@author: asus
'''
import os

from componentProxy.abstractDockerModelCreator import AbstractContainerModelCreator
from docker_letv.docker_model import Docker_Model

class MysqlDockerModelCreator(AbstractContainerModelCreator):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
    
    def create(self, arg_dict):
        '''
        @todo: 
        1. validate the field should be
        2. specify the default value
        '''
        _container_name = arg_dict.get('container_name')
        _containerClusterName = arg_dict.get('containerClusterName')
        _env = eval(arg_dict.get('env'))
        _image_version = arg_dict.get('image_version')
        _image_name = arg_dict.get('image_name')
        _image = '%s:%s' % (_image_name, _image_version)
        _mem_limit = int(arg_dict.get('mem_limit'))
        _volumes = eval(arg_dict.get('volumes'))
        _binds = eval( arg_dict.get('binds'))
        _binds = self.__rewrite_bind_arg(_containerClusterName, _binds)
        _ports = arg_dict.get('ports')
        _network_mode = arg_dict.get('network_mode')
        
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
        if 'ip' == _network_mode:
            _docker_model.use_ip = True
        
        return _docker_model
    
    '''
    @todo: 
    1. remove the os.mkdir
    2. put this logic to container_opers
    '''
    def __rewrite_bind_arg(self, containerClusterName, bind_arg):
        re_bind_arg = {}
        for k,v in bind_arg.items():
            if '/data/mcluster_data' in k:
                _path = '/data/mcluster_data/d-mcl-%s' % containerClusterName
                if not os.path.exists(_path):
                    os.mkdir(_path)
                re_bind_arg.setdefault(_path, v)
            else:
                re_bind_arg.setdefault(k, v)
        return re_bind_arg
        