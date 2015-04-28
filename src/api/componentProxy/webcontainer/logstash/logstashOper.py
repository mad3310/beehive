#-*- coding: utf-8 -*-


from componentProxy.baseComponentOpers import BaseComponentManager


class LogstashManager(BaseComponentManager):

    def __init__(self):
        super(LogstashManager, self).__init__('logstash-manager')

    def manager_status(self, container_name = None):
        return True