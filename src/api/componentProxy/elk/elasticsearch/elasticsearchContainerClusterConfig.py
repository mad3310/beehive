__author__ = 'xsank'


from componentProxy.baseClusterConfig import BaseContainerClusterConfig


class ElasticsearchContainerClusterConfig(BaseContainerClusterConfig):
    '''
    classdocs
    '''

    def __init__(self, params={}):
        super(ElasticsearchContainerClusterConfig, self).__init__(params)

        node_count = params.get('nodeCount')
        self.nodeCount = int(node_count) if node_count else 3
        image = params.get('image')
        self.image = image if image else '10.160.140.32:5000/elasticsearch:0.0.1'
        ports = params.get('ports')
        self.ports = eval(ports) if ports else [9200,9300,9999]

        logs_bind = '/var/log/%s' % self.container_cluster_name
        data_bind = '/data/esdata/%s' % self.container_cluster_name
        default_mount_dir = [{'/var/log': logs_bind, 'ro' : False}, {'/data': data_bind, 'ro' : False}]

        mount_dir = params.get('mountDir')
        self.mount_dir = eval(mount_dir) if mount_dir else default_mount_dir