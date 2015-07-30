'''
Created on 2015-2-4

@author: asus
'''
import logging
from zk.zkOpers import Container_ZkOpers
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
        zkOper = Container_ZkOpers()
        
        container_node_list = zkOper.retrieve_container_list(cluster)
        status_list, result = [], {}
        for container_node in container_node_list:
            status_node_value = zkOper.retrieve_container_status_value(cluster, container_node)
            status_list.append(status_node_value.get('status'))
        
        status = self.__get_cluster_status(status_list)
        result.setdefault('status', status)
        
        if status == Status.destroyed:
            logging.info('delete containerCluster: %s record in zookeeper' % cluster)
            zkOper.delete_container_cluster(cluster)

        return result

    def __get_cluster_status(self, status_list):
        
        cluster_stat = ''
        
        status_set_len = len(set(status_list))
        if status_set_len == 1:
            stat = status_list.pop()
            if stat in Status:
                cluster_stat = stat
            else:
                cluster_stat = Status.failed
        elif status_set_len == 0:
            cluster_stat = Status.destroyed
        else:
            i = 0
            for status in status_list:
                if status == Status.started:
                    i += 1
            
            if i >= 3:
                cluster_stat = Status.started
            elif i == 2:
                cluster_stat = Status.danger
            elif i ==1:
                cluster_stat = Status.crisis
            else:
                cluster_stat = Status.failed
                
        return cluster_stat
