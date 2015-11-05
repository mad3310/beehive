__author__ = 'xsank'


from componentProxy.baseComponentOpers import BaseComponentManager


class ElasticsearchManager(BaseComponentManager):

    def __init__(self):
        super(ElasticsearchManager, self).__init__('logs-manager')

    def manager_status(self, container_name = None):
        return True