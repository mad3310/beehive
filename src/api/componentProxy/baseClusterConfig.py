'''
Created on 2015-2-5

@author: asus
'''

class BaseContainerClusterConfig(object):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        '''
        Constructor
        '''
        
        self.is_res_verify = True
        self.need_validate_manager_status = True

        nodeCount = params.get('nodeCount')                          
        self.nodeCount = int(nodeCount) if nodeCount else 1
        
        """
            default value stand for 10G
            server rest minimum memory 
        """       
        mem_free_limit = params.get('memFree')                          
        self.mem_free_limit = mem_free_limit if mem_free_limit else 10*1024*1024*1024
        
        """
            default value stand for 512M
            container memory limit
        """
        mem_limit = params.get('memory')                           
        self.mem_limit = mem_limit if mem_limit else 512*1024*1024
        
        disk_usage = params.get('diskUsage')
        self.disk_usage = float(disk_usage) if disk_usage else 0.8

        container_cluster_name = params.get('containerClusterName')
        self.container_cluster_name = container_cluster_name
        component_type = params.get('componentType')
        self.component_type = component_type
        network_mode = params.get('networkMode')
        self.network_mode = network_mode

#         image = params.get('image')
#         self.image = image if image else 'letv/mcluster:0.0.2'
#         data_bind = '/data/mcluster_data/d-mcl-%s' % self.container_cluster_name
#         self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':data_bind}
#         self.ports = [2181,2888,3306,3888,4567,4568,4569]