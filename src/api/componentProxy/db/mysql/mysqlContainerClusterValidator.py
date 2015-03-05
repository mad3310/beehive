#-*- coding: utf-8 -*-

import logging

from zk.zkOpers import ZkOpers


class MysqlContainerClusterValidator():
    
    zk_oper = ZkOpers()
    
    def validate_container_cluster_status(self, cluster):
        container_ip_list = self.zk_oper.retrieve_container_list(cluster)
        status_list, cluster_status = [], {}
        for container_ip in container_ip_list:
            status = self.zk_oper.retrieve_container_status_value(cluster, container_ip)
            status_list.append(status.get('status'))
        
        ret = self.__get_cluster_status(status_list)
        cluster_status.setdefault('status', ret)
        if ret == 'destroyed':
            logging.info('delete containerCluster: %s' % cluster)
            self.zk_oper.delete_container_cluster(cluster)
        return cluster_status

    def __get_cluster_status(self, status_list):
        
        cluster_stat = ''
        stat_set = ['starting', 'started', 'stopping', 'stopped', 'destroying', 'destroyed']
        normal_nodes_stat, all_nodes_stat = [], []
        
        if len(set(status_list)) == 1:
            stat = status_list.pop()
            if stat in stat_set:
                cluster_stat = stat
            else:
                cluster_stat = 'failed'
        else:
            i = 0
            for status in status_list:
                if status == 'started':
                    i += 1
            if i == 2:
                cluster_stat = 'danger'
            elif i ==1:
                cluster_stat = 'crisis'
            else:
                cluster_stat = 'failed'
        return cluster_stat