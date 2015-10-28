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
        self.image = image if image else '10.160.140.32:5000/logstash2:0.0.1'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [5043]

        logs_bind = '/var/log/%s' % self.container_cluster_name
        default_mount_dir = [{'/var/log': logs_bind, 'ro' : False}, {'data': '/data', 'ro' : False}]
        
        mount_dir = params.get('mountDir')
        self.mount_dir = eval(mount_dir) if mount_dir else default_mount_dir