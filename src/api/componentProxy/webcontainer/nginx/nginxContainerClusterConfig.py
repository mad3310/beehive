#-*- coding: utf-8 -*-

'''
Created on 2015-3-9

@author: asus
'''

class NginxContainerClusterConfig(object):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        self.__init_params(params)
    
    def __init_params(self, params={}):
            
        self.is_res_verify = False
        self.nodeCount = 1
        self.need_validate_manager_status = False
        
        """
            default value stand for 10G
            server rest minimum memory 
        """
        self.mem_free_limit = 10*1024*1024*1024
        
        """
            default value stand for 512M
            container rest minimum memory
        """
        
        mem_limit = params.get('mem_limit')                          
        self.mem_limit = mem_limit if mem_limit else 512*1024*1024
        
        image = params.get('image')
        self.image = image if image else 'nginx/mcluster:0.0.1'
        
        container_cluster_name = params.get('containerClusterName')
        self.container_cluster_name = container_cluster_name
        component_type = params.get('componentType')
        self.component_type = component_type
        network_mode = params.get('network_mode')
        self.network_mode = network_mode
        self.ports = [2181]    ##for test