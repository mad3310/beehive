#-*- coding: utf-8 -*-

'''
Created on 2015-3-9

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class LogstashContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        super(LogstashContainerClusterConfig, self).__init__(params)
            
        nodeCount = params.get('nodeCount')                          
        self.nodeCount = int(nodeCount) if nodeCount else 1
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/letv/base-jetty:logstash-0.0.1'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [5601]