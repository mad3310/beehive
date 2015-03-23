'''
Created on 2015-2-5

@author: asus
'''
from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class MysqlContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        super(MysqlContainerClusterConfig, self).__init__(params)
        self.__init_params(params)

        data_bind = '/data/mcluster_data/d-mcl-%s' % self.container_cluster_name
        self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':data_bind}
        self.ports = [2181,2888,3306,3888,4567,4568,4569]        

#     def __init_params(self, params):
#             
#         self.is_res_verify = True
#         self.nodeCount = 3
#         self.need_validate_manager_status = True
#         
#         self.mem_free_limit = 1*1024*1024*1024                      #default value stand for 10G                  
#         mem_limit = params.get('memLimit')                          #default value stand for 512M
#         self.mem_limit = mem_limit if mem_limit else 512*1024*1024
#         
#         disk_usage = params.get('diskUsage')
#         self.disk_usage = float(disk_usage) if disk_usage else 0.8
# 
#         image = params.get('image')
#         self.image = image if image else 'letv/mcluster:0.0.2'
# 
#         container_cluster_name = params.get('containerClusterName')
#         self.container_cluster_name = container_cluster_name
#         component_type = params.get('componentType')
#         self.component_type = component_type
#         network_mode = params.get('networkMode')
#         self.network_mode = network_mode
#         
#         data_bind = '/data/mcluster_data/d-mcl-%s' % self.container_cluster_name
#         self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':data_bind}
#         self.ports = [2181,2888,3306,3888,4567,4568,4569]