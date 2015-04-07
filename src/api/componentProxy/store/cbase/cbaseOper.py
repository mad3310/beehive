#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class GbalancerManager(BaseComponentManager):

    def __init__(self):
        super(GbalancerManager, self).__init__('cbase-manager')
    
    def manager_status(self, container_name = None):
        return True