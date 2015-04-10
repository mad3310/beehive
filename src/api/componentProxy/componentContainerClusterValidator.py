'''
Created on 2015-2-4

@author: asus
'''
import logging
from zk.zkOpers import ZkOpers
from status.status_enum import Status
from utils.exceptions import UserVisiableException
from container.container_module import Container


class ComponentContainerClusterValidator(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
    
    def container_cluster_status_validator(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
        
        if not exists:
            raise UserVisiableException('containerCluster %s not existed' % containerClusterName)
        
        create_successful = {'code':"000000"}
        creating = {'code':"000001", 'status': Status.creating}
        create_failed = {'code':"000002", 'status': Status.create_failed}
        
        result = {}
        
        zkOper = ZkOpers()
        try:
            container_cluster_info = zkOper.retrieve_container_cluster_info(containerClusterName)
        finally:
            zkOper.close()
        
        start_flag = container_cluster_info.get('start_flag')
        
        if not start_flag:
            return creating
        else:
            if start_flag == Status.failed:
                result.update(create_failed)
                result.setdefault('error_msg', 'create containers failed!')
            
            elif start_flag == Status.succeed:
                cluster_status_info = self.cluster_status_info(containerClusterName)
                result.update(create_successful)
                result.update(cluster_status_info)
            
            return result

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

    def cluster_status_info(self, cluster):
        zkOper = ZkOpers()
        message_list = []
        try:
            container_node_list = zkOper.retrieve_container_list(cluster)
            status_list, result = [], {}
            for container_node in container_node_list:
                container_node_value = self.__get_create_info(cluster, container_node)
                message_list.append(container_node_value)
                status_node_value = zkOper.retrieve_container_status_value(cluster, container_node)
                status_list.append(status_node_value.get('status'))
            
            status = self.__get_cluster_status(status_list)
            result.setdefault('containers', message_list)
            result.setdefault('status', status)
            
            if status == Status.destroyed:
                logging.info('delete containerCluster: %s record in zookeeper' % cluster)
                zkOper.delete_container_cluster(cluster)
        finally:
            zkOper.close()
            
        return result

    def __get_create_info(self, containerClusterName, container_node):
        zkOper = ZkOpers()
        try:
            container_node_value = zkOper.retrieve_container_node_value(containerClusterName, container_node)
        finally:
            zkOper.close()
        
        con = Container()
        create_info = con.create_info(container_node_value)
        return create_info
