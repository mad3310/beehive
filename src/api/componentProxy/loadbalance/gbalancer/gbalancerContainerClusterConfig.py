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

        super(GbalancerContainerClusterConfig, self).__init__(params)
        
        self.nodeCount = 1
        image = params.get('image')
        self.image = image if image else 'letv/mcluster_vip_gbalancer:0.0.3'