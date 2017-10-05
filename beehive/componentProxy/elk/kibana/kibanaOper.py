__author__ = 'xsank'


from componentProxy.baseComponentOpers import BaseComponentManager


class KibanaManager(BaseComponentManager):

    def __init__(self):
        super(KibanaManager, self).__init__('logs-manager')

    def manager_status(self, container_name = None):
        return True