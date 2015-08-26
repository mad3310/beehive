__author__ = 'mazheng'

from componentProxy.baseComponentOpers import BaseComponentManager


class ZookeeperManager(BaseComponentManager):

    def __init__(self):
        super(ZookeeperManager,self).__init__('zookeeper-manager')