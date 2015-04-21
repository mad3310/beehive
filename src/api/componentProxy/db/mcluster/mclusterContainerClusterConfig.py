'''
Created on 2015-2-5

@author: asus
'''
from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class MclusterContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        super(MclusterContainerClusterConfig, self).__init__(params)
        
        nodeCount = params.get('nodeCount')
        self.nodeCount = int(nodeCount) if nodeCount else 3
        image = params.get('image')
        self.image = image if image else 'letv/mcluster:0.0.2'
        
        data_bind = '/data/mcluster_data/d-mcl-%s' % self.container_cluster_name
        self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':data_bind}
        self.ports = [2181,2888,3306,3888,4567,4568,4569]
        
        self.resource_weight__score = { 'memory': 20, 'disk': 20, 'load5': 20, 'load10': 10, 'load15': 5, 'container_number': 15 }