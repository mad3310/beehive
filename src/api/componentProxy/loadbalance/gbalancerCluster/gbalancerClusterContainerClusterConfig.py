'''
Created on 2015-2-5

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class GbalancerclusterContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''


    def __init__(self, params={}):

        super(GbalancerclusterContainerClusterConfig, self).__init__(params)
        
        nodeCount = params.get('nodeCount')
        self.nodeCount = int(nodeCount) if nodeCount else 2
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/letv/gbalancer-cluster:0.0.9'
        #lib_modules_bind = '/lib/modules/2.6.32-925.431.23.3.letv.el6.x86_64'
        lib_modules_bind = '/lib/modules/2.6.32-925.431.29.2.letv.el6.x86_64'
        self.mount_dir = {lib_modules_bind:lib_modules_bind}