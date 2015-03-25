#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class GbalancerManager(BaseComponentManager):

    def __init__(self):
        super(GbalancerManager, self).__init__('gbalancer-manager')
