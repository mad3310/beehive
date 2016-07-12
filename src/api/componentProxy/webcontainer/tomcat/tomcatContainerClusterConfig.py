#-*- coding: utf-8 -*-

'''
Created on 2015-3-9

@author: asus
'''

from componentProxy.baseClusterConfig import BaseContainerClusterConfig

class TomcatContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        super(TomcatContainerClusterConfig, self).__init__(params)
            
        nodeCount = params.get('nodeCount')
        self.nodeCount = int(nodeCount) if nodeCount else 1
        self.need_validate_manager_status = False
        image = params.get('image')
        self.image = image
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [8888, 9888, 9999, 7777]

        
        #logs_bind = '/var/log/%s' % self.container_cluster_name
        #default_mount_dir = [{'/var/log': logs_bind, 'ro' : False}]
        default_mount_dir = [{'/var/log': '', 'ro' : False}]
        
        mount_dir = params.get('mountDir')
        self.mount_dir = eval(mount_dir) if mount_dir else default_mount_dir
