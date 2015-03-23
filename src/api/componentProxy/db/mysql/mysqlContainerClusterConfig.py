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
        
        nodeCount = params.get('nodeCount')                          
        self.nodeCount = int(nodeCount) if nodeCount else 3
        image = params.get('image')
        self.image = image if image else 'letv/mcluster:0.0.2'
        
        data_bind = '/data/mcluster_data/d-mcl-%s' % self.container_cluster_name
        self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':data_bind}
        self.ports = [2181,2888,3306,3888,4567,4568,4569]