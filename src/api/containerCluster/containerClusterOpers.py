#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import random, re
import logging, traceback

from utils.autoutil import getHostIp, http_get
from tornado.options import options
from common.abstractContainerOpers import Abstract_Container_Opers
from utils.exceptions import UserVisiableException
from utils import _retrieve_userName_passwd
from container.container_module import Container
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
            raise UserVisiableException('param not correct, no containerClusterName param')
        
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
        
        if not exists:
            raise UserVisiableException('containerCluster %s not existe, no need to remove' % containerClusterName)
        
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
        
        if not self.check_cluster_in_zk(containerClusterName):
            return {'status': Status.not_exist}
        
        component_type = self.__get_component_type(containerClusterName)
        cluster_status = self.component_container_cluster_validator.container_cluster_status_validator(component_type,
                                                                                                       containerClusterName)
        return cluster_status

    def check_cluster_in_zk(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            container_ip_list = zkOper.retrieve_container_list(containerClusterName)
        finally:
            zkOper.close()
        
        return len(container_ip_list) != 0
        
    def __get_component_type(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            container_ip_list = zkOper.retrieve_container_list(containerClusterName)
            container_ip = container_ip_list[0]
            con_info = zkOper.retrieve_container_node_value(containerClusterName, container_ip)
        finally:
            zkOper.close()
        
        return con_info.get('type')

    def __get_create_info(self, containerClusterName, container_node):
        zkOper = ZkOpers()
        try:
            container_node_value = zkOper.retrieve_container_node_value(containerClusterName, container_node)
        finally:
            zkOper.close()
        
        con = Container()
        create_info = con.create_info(container_node_value)
        return create_info

    def create_status(self, containerClusterName):
        zkOper = ZkOpers()
        try:
            exists = zkOper.check_containerCluster_exists(containerClusterName)
        finally:
            zkOper.close()
        
        if not exists:
            raise UserVisiableException('containerCluster %s not existed' % containerClusterName)
        
        failed_rst = {'code':"000001"}
        succ_rst = {'code':"000000"}
        lack_rst = {'code':"000002"}
        check_rst_dict, message_list  = {}, []
        
        zkOper = ZkOpers()
        try:
            container_node_list = zkOper.retrieve_container_list(containerClusterName)
            container_cluster_info = zkOper.retrieve_container_cluster_info(containerClusterName)
        finally:
            zkOper.close()
        
        start_flag = container_cluster_info.get('start_flag')
        
        if not start_flag:
            return failed_rst
        else:
            if start_flag == Status.succeed:
                for container_node in container_node_list:
                    container_node_value = self.__get_create_info(containerClusterName, container_node)
                    message_list.append(container_node_value)
                check_rst_dict.update(succ_rst)
                check_rst_dict.setdefault('containers', message_list)
                check_rst_dict.setdefault('message', 'check all containers OK!')
            
            elif  start_flag == 'lack_resource':
                check_rst_dict.update(lack_rst)
                check_rst_dict.setdefault('error_msg', container_cluster_info.get('error_msg'))
                logging.info('return info:%s' % str(check_rst_dict))
            
            elif start_flag == Status.failed:
                check_rst_dict.update(lack_rst)
                check_rst_dict.setdefault('error_msg', 'create containers failed!')
            
            return check_rst_dict

    def config(self, conf_dict={}):
        try:
            error_msg = ''
            logging.info('config args: %s' % conf_dict)
            
            if 'servers' in conf_dict:
                error_msg = self.__update_white_list(conf_dict)
            else:
                error_msg = 'the key of the params is not correct'
        except:
            error_msg = str( traceback.format_exc() )
            logging.error( error_msg )
        finally:
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

    def __rewrite_conf_info(self, conf_dict, conf_record):
        for key, value in conf_dict.items():
            if key == 'mem_limit':
                value = eval(value)
            if key in conf_record:
                conf_record[key] = value
            else:
                conf_record.setdefault(key, value)
        return conf_record

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
                container_node.setdefault('create_info', create_info)
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


class GetLastestClustersInfo(object):
    """
        webportal do info sync every 10 minutes,
        then interface will invoke this class
    """
    def __init__(self):
        '''
        Constructor
        '''
        
    def get_res(self):
        host_ip = self.__random_host_ip()
        self._get(host_ip, '/serverCluster/update')
        res = self._get(host_ip, '/containerCluster/info')
        logging.info('res : %s' % str(res) )
        return self.__reget_res(res)
    
    def __random_host_ip(self):
        zkOper = ZkOpers()
        
        try:
            host_ip_list = zkOper.retrieve_data_node_list()
        finally:
            zkOper.close()
            
        host = getHostIp()
        if host in host_ip_list:
            host_ip_list.remove(host)
        host_ip = random.choice(host_ip_list)
        return host_ip
    
    def _get(self, host_ip, url_get):
        adminUser, adminPasswd = _retrieve_userName_passwd()
        uri = 'http://%s:%s%s' % (host_ip, options.port, url_get)
        logging.info('get uri :%s' % uri)
        ret = http_get(uri, auth_username = adminUser, auth_password = adminPasswd)
        return ret.get('response')

    def __reget_res(self, res):
        clusters = []
        for cluster_name, nodes in res.items():
            cluster, nodeInfo = {}, []
            cluster_exist = self.__get_cluster_status(nodes)
            cluster.setdefault('status', cluster_exist)
            cluster.setdefault('clusterName', cluster_name)
            for _,node_value in nodes.items():
                create_info = node_value.get('create_info')
                con = Container()
                create_info = con.create_info(create_info)
                nodeInfo.append(create_info)
            cluster.setdefault('nodeInfo', nodeInfo)
            clusters.append(cluster)
        return clusters
    
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
