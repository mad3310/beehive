'''
Created on Sep 8, 2014

@author: root
'''
import logging
import traceback
import docker

from api.common.abstractContainerOpers import Abstract_Container_Opers

class Container_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        '''
        Constructor
        '''
    def create(self, dict):
        container_ip = dict.get('containerIp')
        logging.debug('container ip is %s' % container_ip)
        
        container_name = dict.get('containerName')
        logging.debug('create container %s' % container_name)
        
        container_type = dict.get('containerType')
        
        image_name = 'letv/vip:0.0.1'
        if 'mclusternode' == container_type:
            image_name = 'letv/mcluster:0.0.3'
        
        logging.debug('the env:%s' % str(dict))
        try:
            c = docker.Client('unix://var/run/docker.sock', timeout = 10)
            c.create_container(image=image_name, command='true', hostname=container_name, user='root',
                               name=container_name, environment=dict, tty=True, 
                               mem_limit=None, volumes=None, volumes_from=None)
            
            c.start(container_name)
            print c.containers(all=True)
        except: 
            logging.error('the exception of creating container:%s' % traceback.format_exc())
            return False
        
        result = self._check_container_status(c)
        if not result:
            logging.error('the exception of creating container')
            return False
        
        dict = {}
        dict.setdefault('containerClusterName', container_name)
        dict.setdefault('containerNodeIP', container_ip)
        
        self.zkOper.writer_container_node_info(dict)
        return True
    
    def destory(self):
        pass
    
    def _check_container_status(self, client):
        return True
