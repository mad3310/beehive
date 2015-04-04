'''
Created on 2015-2-4

@author: asus
'''
import logging
from zk.zkOpers import ZkOpers
from status.status_enum import Status


class ComponentContainerClusterValidator(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''

    def container_cluster_status_validator(self, cluster):
        zkOper = ZkOpers()
        
        try:
            container_ip_list = zkOper.retrieve_container_list(cluster)
            status_list, cluster_status = [], {}
            for container_ip in container_ip_list:
                status = zkOper.retrieve_container_status_value(cluster, container_ip)
                status_list.append(status.get('status'))
            
            ret = self.__get_cluster_status(status_list)
            cluster_status.setdefault('status', ret)
            if ret == Status.destroyed:
                logging.info('delete containerCluster: %s' % cluster)
                zkOper.delete_container_cluster(cluster)
        finally:
            zkOper.close()
            
        return cluster_status

    def __get_cluster_status(self, status_list):
        
        cluster_stat = ''
        
        if len(set(status_list)) == 1:
            stat = status_list.pop()
            if stat in Status:
                cluster_stat = stat
            else:
                cluster_stat = Status.failed
        else:
            i = 0
            for status in status_list:
                if status == Status.started:
                    i += 1
            if i == 2:
                cluster_stat = Status.danger
            elif i ==1:
                cluster_stat = Status.crisis
            else:
                cluster_stat = Status.failed
        return cluster_stat
