#-*- coding: utf-8 -*-

'''
Created on 2015-3-9

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class JettyContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        super(JettyContainerClusterConfig, self).__init__(params)
            
        nodeCount = params.get('nodeCount')                          
        self.nodeCount = int(nodeCount) if nodeCount else 2
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/letv/base-jetty:0.0.3'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [8888, 9888]
        
        mount_dir = params.get('mountDir')
        logs_bind = '/var/log/%s' % self.container_cluster_name
        self.mount_dir = eval(mount_dir) if mount_dir else {'/var/log': logs_bind}