#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class CbaseManager(BaseComponentManager):

    def __init__(self):
        super(CbaseManager, self).__init__('cbase', "service cbase status", 'couchbase-server is running')