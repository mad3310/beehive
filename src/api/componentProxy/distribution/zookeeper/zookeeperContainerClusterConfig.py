__author__ = 'mazheng'

from componentProxy.baseClusterConfig import BaseContainerClusterConfig


class ZookeeperContainerClusterConfig(BaseContainerClusterConfig):

    def __init__(self,params={}):
        super(ZookeeperContainerClusterConfig,self).__init__(params)

        node_count=params.get('nodeCount')
        self.nodeCount = int(node_count) if node_count else 3
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/letv-zookeeper:0.0.1'
        self.ports = [2181, 2888, 3888, 4567, 4568, 4569]

        self.resource_weight__score = { 'memory': 20, 'disk': 20, 'load5': 20, 'load10': 10, 'load15': 5, 'container_number': 15 }