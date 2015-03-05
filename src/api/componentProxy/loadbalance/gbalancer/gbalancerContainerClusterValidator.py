#-*- coding: utf-8 -*-

import logging

from zk.zkOpers import ZkOpers


class GbalancerContainerClusterValidator():
    
    zk_oper = ZkOpers()
    
    def validate_container_cluster_status(self, cluster):
        container_ip_list = self.zk_oper.retrieve_container_list(cluster)
        container_ip = container_ip_list[0]
        status = self.zk_oper.retrieve_container_status_value(cluster, container_ip)
        status = status.get('status')
        
        cluster_status.setdefault('status', status)
        if status == 'destroyed':
            logging.info('delete containerCluster: %s' % containerClusterName)
            self.zk_oper.delete_container_cluster(containerClusterName)
        return cluster_status