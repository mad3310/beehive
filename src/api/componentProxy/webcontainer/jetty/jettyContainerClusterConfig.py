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
        self.nodeCount = int(nodeCount) if nodeCount else 1
        image = params.get('image')
        self.image = image if image else 'letv/jetty:0.0.1'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [8080, 8888, 9888]