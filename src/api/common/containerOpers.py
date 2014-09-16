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
        
        container_node_info = self._get_container_node_info(arg_dict)
        logging.info('send to liuhao: %s' % str(container_node_info))
        
        create_result = self.create_container(arg_dict)
        
        if create_result:
            logging.info('create container successful, write info!')
            self.zkOper.write_container_node_info(container_node_info)
        
        
    def create_container(self, arg_dict={}):
        
        container_ip = arg_dict.get('container_ip')
        container_name = arg_dict.get('container_name')
        container_type = arg_dict.get('container_type')
        _volumes = arg_dict.get('volumes')
        env = eval(arg_dict.get('env'))
        
        logging.info('container_ip: %s' % str(container_ip))
        logging.info('container_name: %s' % container_name)
        logging.info('container_type: %s' % container_type)
        logging.info('env: %s' % str(env) )
        
        if container_type == 'mclusternode':
            image_name = 'letv/mcluster:0.0.3'
        else:
            image_name = 'letv/vip:0.0.3'
        
        _ports = [(3306, 'tcp'), (4567, 'tcp'), (4568, 'tcp'), (4569, 'tcp'), (2181, 'tcp'), (2888, 'tcp'), (3888, 'tcp')]
        volume_path = '/srv/docker/vfs/dir/%s' % container_name
        
#         if not os.path.exists(volume_path):
#             os.mkdir(volume_path)
            
        try:
            c = docker.Client('unix://var/run/docker.sock')
            container_id = c.create_container(image=image_name, hostname=container_name, user='root',
                                              name=container_name, environment=env, tty=True, ports=_ports, stdin_open=True,
                                              mem_limit='1g', volumes=_volumes, volumes_from=None)
            
            c.start(container_name, privileged=True, network_mode='bridge', 
                    binds={ '/data/mcluster_data/d-mcl-clvimysql3309':{'bind':'/data/mcluster_data'},
                            #volume_path:{'bind':'/srv/mcluster'}
                            } ,
                    port_bindings={3306: '', 4567: '', 4568: '', 4569: '', 2181: '', 2888: '', 3888: ''}
                    )
            
            logging.info( 'c.container: %s' % str( c.containers(latest=True)))
        except:
            logging.error('the exception of creating container:%s' % str(traceback.format_exc()))
            return False
        
        result = self._check_container_status(c)
        if not result:
            logging.error('the exception of creating container')
            return False
        return True
    
    def _get_container_node_info(self, arg_dict={}):
        env = eval(arg_dict.get('env'))
        container_node_info= {}
        container_node_info.setdefault('containerClusterName', arg_dict.get('containerClusterName'))
        container_node_info.setdefault('containerNodeIP', arg_dict.get('container_ip'))
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
    
    
    
    
    
    