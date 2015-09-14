#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''

import re

from containerClusterAction import *
from common.abstractContainerOpers import Abstract_Container_Opers
from utils.exceptions import UserVisiableException
from container.container_model import Container_Model
from zk.zkOpers import Requests_ZkOpers
from componentProxy.componentContainerClusterValidator import ComponentContainerClusterValidator
from utils.threading_exception_queue import Threading_Exception_Queue


class ContainerCluster_Opers(Abstract_Container_Opers):
    
    component_container_cluster_validator = ComponentContainerClusterValidator()
    threading_exception_queue = Threading_Exception_Queue()
        
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, args):
        cluster = args.get('containerClusterName', None)
        if not cluster:
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        if not args.has_key('networkMode'):
            raise UserVisiableException('params networkMode not be given, please check the params!')
        if not args.has_key('componentType'):
            raise UserVisiableException('params componentType not be given, please check the params!')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if exists:
            raise UserVisiableException('containerCluster %s has existed, choose another containerCluster name' % cluster)
        
        containerCluster_create_action = ContainerCluster_create_Action(args)
        containerCluster_create_action.start()

    def add(self, args):
        cluster = args.get('containerClusterName', None)
        if not cluster:
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        node_count = args.get('nodeCount') 
        if not node_count:
            raise UserVisiableException('params nodeCount not be given, please check the params!')        
        if not args.has_key('networkMode'):
            raise UserVisiableException('params networkMode not be given, please check the params!')
        if not args.has_key('componentType'):
            raise UserVisiableException('params componentType not be given, please check the params!')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if not exists:
            raise UserVisiableException('cluster %s not exist, you should give a existed cluster when add node to it!' % cluster)
        
        containerCluster_create_action = ContainerCluster_Add_Action(args)
        containerCluster_create_action.start()

    def remove(self, args):
        """
            remove node in some cluster
        """
        
        cluster = args.get('containerClusterName')
        if not cluster:
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        containers = args.get('containerNameList')
        if not containers:
            raise UserVisiableException('params containerNameList not be given, please check the params!')

        _containers = containers.split(',')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed, no need to remove' % cluster)
        
        containerCluster_remove_node_action = ContainerCluster_RemoveNode_Action(cluster, _containers)
        containerCluster_remove_node_action.start()

    def start(self, containerClusterName):
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise UserVisiableException('containerCluster %s not exist, choose another containerCluster name' % containerClusterName)
        
        containerCluster_start_action = ContainerCluster_start_Action(containerClusterName)
        containerCluster_start_action.start()

    def stop(self, containerClusterName):
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed, choose another containerCluster name' % containerClusterName)
        
        containerCluster_stop_action = ContainerCluster_stop_Action(containerClusterName)
        containerCluster_stop_action.start()

    def destory(self, containerClusterName):
        if not containerClusterName:
            raise UserVisiableException('no containerClusterName param')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed, no need to remove' % containerClusterName)
        
        containerCluster_destroy_action = ContainerCluster_destroy_Action(containerClusterName)
        containerCluster_destroy_action.start()

    def check(self, containerClusterName):
        zkOper = Requests_ZkOpers()
        exists = zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed' % containerClusterName)
        
        cluster_status = self.component_container_cluster_validator.container_cluster_status_validator(containerClusterName)
        return cluster_status

    def sync(self):
        clusters_zk_info = self.get_clusters_zk()
        
        clusters = []
        for cluster_name, nodes in clusters_zk_info.items():
            try:
                cluster, nodeInfo = {}, []
                logging.info('sync action, cluster name:%s' % cluster)
                cluster_status = self.component_container_cluster_validator.container_cluster_status_validator(cluster_name)
                cluster.setdefault('status', cluster_status)
                cluster.setdefault('clusterName', cluster_name)
                
                zkOper = Requests_ZkOpers()
                cluster_info = zkOper.retrieve_container_cluster_info(cluster_name)
                _type = cluster_info.get('type')
                cluster.setdefault('type', _type)
                
                for _,node_value in nodes.items():
                    container_info = node_value.get('container_info')
                    con = Container_Model()
                    create_info = con.create_info(container_info)
                    nodeInfo.append(create_info)
                cluster.setdefault('nodeInfo', nodeInfo)
                clusters.append(cluster)
                
            except:
                self.threading_exception_queue.put(sys.exc_info())
                continue
            
        return clusters

    def config(self, conf_dict={}):
        error_msg = ''
        logging.info('config args: %s' % conf_dict)
        
        if 'servers' in conf_dict:
            error_msg = self.__update_white_list(conf_dict)
        else:
            error_msg = 'the key of the params is not correct'
        return error_msg

    def __update_white_list(self, conf_dict):
        error_msg = ''
        conf_white_str = conf_dict.get('servers')
        ip_pattern = '(((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?),)+((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)'
        if not re.match(ip_pattern, conf_white_str):
            error_msg = 'the values of the params is not correct'
            logging.error(error_msg)
            return error_msg
        
        zkOper = Requests_ZkOpers()
        conf_white_list = conf_white_str.split(',')
        privs_white_list = zkOper.retrieve_servers_white_list()
        add = list( set(conf_white_list) - set(privs_white_list) )
        delete = list( set(privs_white_list) - set(conf_white_list) )
        both = list( set(privs_white_list) & set(conf_white_list) )
        for item in add:
            zkOper.add_server_into_white_list(item)
            
        for item in delete:
            zkOper.del_server_from_white_list(item)
        return error_msg

    def get_clusters_zk(self):
        zkOper = Requests_ZkOpers()
        cluster_name_list = zkOper.retrieve_cluster_list()
        clusters_zk_info = {}
        for cluster_name in cluster_name_list:
            cluster_info_dict = self.get_cluster_zk(cluster_name)
            if not cluster_info_dict:
                continue
            clusters_zk_info.setdefault(cluster_name, cluster_info_dict)
            
        return clusters_zk_info

    def get_cluster_zk(self, cluster_name):
        cluster_zk_info = {}
        zkOper = Requests_ZkOpers()
        container_ip_list = zkOper.retrieve_container_list(cluster_name)
        for container_ip in container_ip_list:
            container_node = {}
            create_info = zkOper.retrieve_container_node_value(cluster_name, container_ip)
            status = zkOper.retrieve_container_status_value(cluster_name, container_ip)
            container_node.setdefault('container_info', create_info)
            container_node.setdefault('status', status)
            cluster_zk_info.setdefault(container_ip, container_node)
        return cluster_zk_info

    def create_result(self, containerClusterName):
        create_successful = {'code':"000000"}
        creating = {'code':"000001"}
        create_failed = {'code':"000002", 'status': Status.create_failed}

        zkOper = Requests_ZkOpers()
        exists = zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed' % containerClusterName)
        
        result = {}

        container_cluster_info = zkOper.retrieve_container_cluster_info(containerClusterName)
        start_flag = container_cluster_info.get('start_flag')

        if start_flag == Status.failed:
            result.update(create_failed)
            result.setdefault('error_msg', 'create containers failed!')
        
        elif start_flag == Status.succeed:
            create_info = self.__cluster_created_info(containerClusterName)
            result.update(create_successful)
            result.update(create_info)
        else:
            result.update(creating)
        return result

    def __cluster_created_info(self, cluster):
        zkOper = Requests_ZkOpers()
        message_list = []
        
        container_node_list = zkOper.retrieve_container_list(cluster)
        result = {}
        for container_node in container_node_list:
            container_node_value = zkOper.retrieve_container_node_value(cluster, container_node)
            con = Container_Model()
            create_info = con.create_info(container_node_value)
            message_list.append(create_info)   
        result.setdefault('containers', message_list)
        return result
