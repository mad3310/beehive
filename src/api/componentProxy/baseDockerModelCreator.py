'''
Created on 2015-2-1

@author: asus
'''
#-*- coding: utf-8 -*-

from docker_letv.docker_model import Docker_Model

class BaseDockerModelCreator(object):
    '''
    classdocs
    '''

    def create(self, arg_dict):
        _container_name = arg_dict.get('container_name')
        _image = arg_dict.get('image')
        _mem_limit = int(arg_dict.get('mem_limit'))
        _network_mode = arg_dict.get('network_mode')
        _host_ip = arg_dict.get('host_ip')
        _component_type = arg_dict.get('component_type')

        _env =  arg_dict.get('env')
        _volumes = arg_dict.get('volumes')
        _binds = arg_dict.get('binds')
        _ports = arg_dict.get('ports')
        _set_network = arg_dict.get('set_network')
        _port_bindings = arg_dict.get('port_bindings')
        _lxc_conf = arg_dict.get('lxc_conf')

        _docker_model = Docker_Model()
        _docker_model.image = _image
        _docker_model.mem_limit = _mem_limit
        _docker_model.host_ip = _host_ip
        _docker_model.component_type = _component_type
        _docker_model.privileged = True
        _docker_model.network_mode = 'bridge'
        _docker_model.name = _container_name
        _docker_model.hostname = _container_name

        if _lxc_conf:
            _docker_model.lxc_conf = eval(_lxc_conf)

        if _set_network:
            _docker_model.set_network = _set_network
        
        if _binds:
            _docker_model.binds = eval(_binds)
        else:
            _docker_model.binds = None
        
        if _volumes:
            _docker_model.volumes = eval(_volumes)
        else:
            _docker_model.volumes = None
        
        if _env:
            _docker_model.environment = eval(_env)
        else:
            _docker_model.environment = None
        
        if _ports:
            _docker_model.ports = eval(_ports)
        else:
            _docker_model.ports = None

        if _port_bindings:
            _docker_model.port_bindings = eval(_port_bindings)
        else:
            _docker_model.port_bindings = None
        
        if 'ip' == _network_mode:
            _docker_model.use_ip = True
        else:
            _docker_model.use_ip = False
        
        return _docker_model
        