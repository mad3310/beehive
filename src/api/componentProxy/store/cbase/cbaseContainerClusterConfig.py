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
        
        nodeCount = params.get('nodeCount')
        self.nodeCount = int(nodeCount) if nodeCount else 1
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/lihanlin1/cbase:V2'
        self.mount_dir = {'/srv':'/srv/tmp/c1/'}