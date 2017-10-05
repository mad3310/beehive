#-*- coding: utf-8 -*-

from componentProxy.baseComponentOpers import BaseComponentManager


class TomcatManager(BaseComponentManager):

    def __init__(self):
        super(TomcatManager, self).__init__('tomcat-manager')
