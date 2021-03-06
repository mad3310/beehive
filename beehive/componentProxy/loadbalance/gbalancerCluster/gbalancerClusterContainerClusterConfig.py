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
        self.image = image if image else '10.160.140.32:5000/letv/gbalancer-cluster:0.0.9'  #0.0.9 for yizhuang, 0.10 for 150 cluster
        
        
        #lib_modules_bind = '/lib/modules/2.6.32-925.431.23.3.letv.el6.x86_64'
        lib_modules_bind = '/lib/modules/2.6.32-925.431.29.2.letv.el6.x86_64'
        logs_bind = '/var/log/%s' % self.container_cluster_name
        default_mount_dir = [{'/var/log': logs_bind, 'ro' : False}, {lib_modules_bind:lib_modules_bind, 'ro' : True}]
        
        mount_dir = params.get('mountDir')
        self.mount_dir = eval(mount_dir) if mount_dir else default_mount_dir
        
        self.set_network = True