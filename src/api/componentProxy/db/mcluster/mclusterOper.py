#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class MclusterManager(BaseComponentManager):

    def __init__(self):
        self.timeout = 5
        super(MclusterManager, self).__init__('mcluster-manager', "curl 'http://127.0.0.1:8888/mcluster/health'", 'ok')