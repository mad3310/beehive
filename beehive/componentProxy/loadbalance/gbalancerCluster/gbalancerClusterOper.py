#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class GbalancerclusterManager(BaseComponentManager):

    def __init__(self):
        super(GbalancerclusterManager, self).__init__('gbalancer-cluster-manager')
    
    def manager_status(self, container_name = None):
        return True
