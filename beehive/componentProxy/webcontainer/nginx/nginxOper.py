#-*- coding: utf-8 -*-


from componentProxy.baseComponentOpers import BaseComponentManager


class NginxManager(BaseComponentManager):

    def __init__(self):
        super(NginxManager, self).__init__('nginx-manager')
