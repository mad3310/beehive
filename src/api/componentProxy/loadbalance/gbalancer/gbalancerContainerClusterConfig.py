'''
Created on 2015-2-5

@author: asus
'''

class GbalancerContainerClusterConfig(object):
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
        self.mem_free_limit = 10*1024*1024*1024                      #default value stand for 10G                  
        mem_limit = params.get('mem_limit')                          #default value stand for 512M
        self.mem_limit = mem_limit if mem_limit else 512*1024*1024

        disk_usage = params.get('diskUsage')
        self.disk_usage = float(disk_usage) if disk_usage else 0.7

        image = params.get('image')
        self.image = image if image else 'letv/mcluster_vip_gbalancer:0.0.3'
        
        container_cluster_name = params.get('containerClusterName')
        self.container_cluster_name = container_cluster_name
        component_type = params.get('componentType')
        self.component_type = component_type
        network_mode = params.get('network_mode')
        self.network_mode = network_mode