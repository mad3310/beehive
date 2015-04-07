#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class CbaseManager(BaseComponentManager):

    def __init__(self):
        super(CbaseManager, self).__init__('cbase-manager')
    
    def manager_status(self, container_name = None):
        return True