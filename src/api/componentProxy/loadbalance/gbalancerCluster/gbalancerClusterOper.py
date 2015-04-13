#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class GbalancerClusterManager(BaseComponentManager):

    def __init__(self):
        super(GbalancerClusterManager, self).__init__('gbalancer-cluster-manager')
    
    def manager_status(self, container_name = None):
        return True
