#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''

import re
import logging

from common.abstractContainerOpers import Abstract_Container_Opers
from utils.exceptions import UserVisiableException
from container.container_model import Container_Model
from zk.zkOpers import ZkOpers
from containerCluster.baseContainerAction import ContainerCluster_Action_Base
from containerCluster.containerClusterCreateAction import ContainerCluster_create_Action
from componentProxy.componentContainerClusterValidator import ComponentContainerClusterValidator
from status.status_enum import Status


class ContainerCluster_Opers(Abstract_Container_Opers):
    
    component_container_cluster_validator = ComponentContainerClusterValidator()
        
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, arg_dict):
        _containerClusterName = arg_dict.get('containerClusterName')
        
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(_containerClusterName)
        finally:
            zkOper.close()
            
        if exists:
            raise UserVisiableException('containerCluster %s has existed, choose another containerCluster name' % _containerClusterName)
        
        containerCluster_create_action = ContainerCluster_create_Action(arg_dict)
        containerCluster_create_action.start()
    
    def start(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
            
        if not exists:
            raise UserVisiableException('containerCluster %s not exist, choose another containerCluster name' % containerClusterName)
        
        containerCluster_start_action = ContainerCluster_start_Action(containerClusterName)
        containerCluster_start_action.start()
        
    def stop(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
            
        if exists:
            raise UserVisiableException('containerCluster %s has existed, choose another containerCluster name' % containerClusterName)
        
        containerCluster_stop_action = ContainerCluster_stop_Action(containerClusterName)
        containerCluster_stop_action.start()

    def destory(self, containerClusterName):
        if not containerClusterName:
            raise UserVisiableException('no containerClusterName param')
        
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
        
        if not exists:
            raise UserVisiableException('containerCluster %s not existed, no need to remove' % containerClusterName)
        
        containerCluster_destroy_action = ContainerCluster_destroy_Action(containerClusterName)
        containerCluster_destroy_action.start()

    def check(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
        
        if not exists:
            raise UserVisiableException('containerCluster %s not existed' % containerClusterName)
        
        cluster_status = self.component_container_cluster_validator.container_cluster_status_validator(containerClusterName)
        return cluster_status

    def sync(self):
        clusters_zk_info = self.get_clusters_zk()
        
        clusters = []
        for cluster_name, nodes in clusters_zk_info.items():
            cluster, nodeInfo = {}, []
            cluster_exist = self.__get_cluster_status(nodes)
            cluster.setdefault('status', cluster_exist)
            cluster.setdefault('clusterName', cluster_name)
            for _,node_value in nodes.items():
                container_info = node_value.get('container_info')
                con = Container_Model()
                create_info = con.create_info(container_info)
                nodeInfo.append(create_info)
            cluster.setdefault('nodeInfo', nodeInfo)
            clusters.append(cluster)
            
        return clusters


    '''
        one cluster status func
    '''
    def __get_cluster_status(self, nodes):
        n = 0
        for _,container_info in nodes.items():
            stat = container_info.get('status').get('status')
            if stat == Status.destroyed:
                n += 1
        if n == len(nodes):
            exist = Status.destroyed
        else:
            exist = Status.alive
        return exist

    def __check_cluster_in_zk(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            container_ip_list = zkOper.retrieve_container_list(containerClusterName)
        finally:
            zkOper.close()
        
        return len(container_ip_list) != 0

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
        
        zkOper = ZkOpers()
        try:
            conf_white_list = conf_white_str.split(',')
            privs_white_list = zkOper.retrieve_servers_white_list()
            add = list( set(conf_white_list) - set(privs_white_list) )
            delete = list( set(privs_white_list) - set(conf_white_list) )
            both = list( set(privs_white_list) & set(conf_white_list) )
            for item in add:
                zkOper.add_server_into_white_list(item)
                
            for item in delete:
                zkOper.del_server_from_white_list(item)
        finally:
            zkOper.close()
            
        return error_msg

    def get_clusters_zk(self):
        zkOper = ZkOpers()
        try:
            cluster_name_list = zkOper.retrieve_cluster_list()
        finally:
            zkOper.close()
        
        clusters_zk_info = {}
        for cluster_name in cluster_name_list:
            cluster_info_dict = self.get_cluster_zk(cluster_name)
            clusters_zk_info.setdefault(cluster_name, cluster_info_dict)
            
        return clusters_zk_info

    def get_cluster_zk(self, cluster_name):
        cluster_zk_info = {}
        
        zkOper = ZkOpers()
        try:
            container_ip_list = zkOper.retrieve_container_list(cluster_name)
        
            for container_ip in container_ip_list:
                container_node = {}
                create_info = zkOper.retrieve_container_node_value(cluster_name, container_ip)
                status = zkOper.retrieve_container_status_value(cluster_name, container_ip)
                container_node.setdefault('container_info', create_info)
                container_node.setdefault('status', status)
                cluster_zk_info.setdefault(container_ip, container_node)
        finally:
            zkOper.close()
        
        return cluster_zk_info


class ContainerCluster_stop_Action(ContainerCluster_Action_Base):

    def __init__(self, containerClusterName):
        super(ContainerCluster_stop_Action, self).__init__(containerClusterName, 'stop')


class ContainerCluster_start_Action(ContainerCluster_Action_Base):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_start_Action, self).__init__(containerClusterName, 'start')


class ContainerCluster_destroy_Action(ContainerCluster_Action_Base):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_destroy_Action, self).__init__(containerClusterName, 'remove')
