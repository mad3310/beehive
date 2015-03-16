#-*- coding: utf-8 -*-

import logging

from zk.zkOpers import ZkOpers
from status.status_enum import Status


class NginxContainerClusterValidator():
    
    zk_oper = ZkOpers()
    
    def validate_container_cluster_status(self, cluster):
        cluster_status = {}
        container_ip_list = self.zk_oper.retrieve_container_list(cluster)
        container_ip = container_ip_list[0]
        status = self.zk_oper.retrieve_container_status_value(cluster, container_ip)
        status = status.get('status')
        
        cluster_status.setdefault('status', status)
        if status == Status.destroyed:
            logging.info('delete containerCluster: %s' % cluster)
            self.zk_oper.delete_container_cluster(cluster)
        return cluster_status