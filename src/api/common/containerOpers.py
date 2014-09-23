'''
Created on Sep 8, 2014

@author: root
'''
import logging
import traceback
import docker
import os

from common.abstractContainerOpers import Abstract_Container_Opers

class Container_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def issue_create_action(self, arg_dict):
        
        container_node_info = self._get_container_info(arg_dict)
        logging.info('get container info: %s' % str(container_node_info))
        
        create_result = self.create_container(arg_dict)
        
        if create_result:
            logging.info('create container successful, write info!')
            self.zkOper.write_container_node_info(container_node_info)
            return
        failed_container_name = arg_dict.get('container_name')
        return failed_container_name
        
    def create_container(self, arg_dict={}):
        
        logging.info('create_container args: %s' % str(arg_dict) )
        container_ip = arg_dict.get('container_ip')
        container_name = arg_dict.get('container_name')
        container_type = arg_dict.get('container_type')
        env = eval(arg_dict.get('env'))
        
        logging.info('container_ip: %s' % str(container_ip))
        logging.info('container_name: %s' % container_name)
        logging.info('container_type: %s' % container_type)
        logging.info('env: %s' % str(env) )
        
        if container_type == 'mclusternode':
            mcluster_info = self.zkOper.retrieve_mcluster_info_from_config()
            version = mcluster_info.get('image_version')
            name = mcluster_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _ports = eval(mcluster_info.get('ports'))
            _mem_limit = mcluster_info.get('mem_limit')
            _volumes = arg_dict.get('volumes')
            _binds = eval( arg_dict.get('binds'))
        
        elif container_type == 'mclustervip':
            mclustervip_info = self.zkOper.retrieve_mclustervip_info_from_config()
            version = mclustervip_info.get('image_version')
            name = mclustervip_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _mem_limit = mclustervip_info.get('mem_limit')
            _binds, _ports, _volumes = None, None, None
        
        try:
            c = docker.Client('unix://var/run/docker.sock')
            container_id = c.create_container(image=image_name, hostname=container_name, user='root',
                                              name=container_name, environment=env, tty=True, ports=_ports, stdin_open=True,
                                              mem_limit=_mem_limit, volumes=_volumes, volumes_from=None)
            c.start(container_name, privileged=True, network_mode='bridge', binds=_binds)
        except:
            logging.error('the exception of creating container:%s' % str(traceback.format_exc()))
            return False
        
        result = self._check_container_status(c)
        if not result:
            logging.error('the exception of creating container')
            return False
        return True
    
    def _get_container_info(self, arg_dict={}):
        env = eval(arg_dict.get('env'))
        container_node_info= {}
        container_node_info.setdefault('containerClusterName', arg_dict.get('containerClusterName'))
        container_node_info.setdefault('containerNodeIP', arg_dict.get('container_ip'))
        container_node_info.setdefault('hostIp', arg_dict.get('host_ip'))
        container_node_info.setdefault('ipAddr', arg_dict.get('container_ip'))
        container_node_info.setdefault('containerName', arg_dict.get('container_name'))
        container_node_info.setdefault('mountDir', arg_dict.get('volumes'))
        container_node_info.setdefault('type', arg_dict.get('container_type'))
        container_node_info.setdefault('zookeeperId', env.get('ZKID'))
        container_node_info.setdefault('netMask', env.get('NETMASK'))
        container_node_info.setdefault('gateAddr', env.get('GATEWAY'))
        return container_node_info
    
    def _check_container_status(self, c):
        latest_result = c.containers(latest=True)
        status = latest_result[0].get('Status')
        if 'Up' in status:
            return True
        return False
    
    def destory(self):
        pass