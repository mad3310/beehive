#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class JettyManager(BaseComponentManager):

    def __init__(self):
        super(JettyManager, self).__init__('jetty-manager')