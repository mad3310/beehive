#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class MclustervipManager(BaseComponentManager):

    def __init__(self):
        super(MclustervipManager, self).__init__('gbalancer-manager')
    
    def manager_status(self, container_name = None):
        return True