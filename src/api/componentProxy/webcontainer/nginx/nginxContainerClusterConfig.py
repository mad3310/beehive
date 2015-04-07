#-*- coding: utf-8 -*-

'''
Created on 2015-3-9

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class NginxContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        super(NginxContainerClusterConfig, self).__init__(params)
            
        nodeCount = params.get('nodeCount')                          
        self.nodeCount = int(nodeCount) if nodeCount else 2
        image = params.get('image')
        self.image = image if image else 'letv/nginx:0.0.4'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [8888, 8001]