'''
Created on 2015-2-5

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class GbalancerContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        self.__init_params(params)
    
    def __init_params(self, params={}):
            
        self.is_res_verify = True
        self.nodeCount = 1
        self.need_validate_manager_status = True
        mem_limit = params.get('memLimit')                          #default value stand for 512M
        
        mem_free_limit = params.get('memFree')                          
        self.mem_free_limit = mem_free_limit if mem_free_limit else 1*1024*1024*1024
        
        self.mem_limit = mem_limit if mem_limit else 512*1024*1024

        disk_usage = params.get('diskUsage')
        self.disk_usage = float(disk_usage) if disk_usage else 0.8

        image = params.get('image')
        self.image = image if image else 'letv/mcluster_vip_gbalancer:0.0.3'
        
        container_cluster_name = params.get('containerClusterName')
        self.container_cluster_name = container_cluster_name
        component_type = params.get('componentType')
        self.component_type = component_type
        network_mode = params.get('networkMode')
        self.network_mode = network_mode