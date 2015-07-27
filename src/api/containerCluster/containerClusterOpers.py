#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''

import re
import logging
import sys

from tornado.options import options
from status.status_enum import Status
from common.abstractContainerOpers import Abstract_Container_Opers
from utils.exceptions import UserVisiableException
from container.container_model import Container_Model
from zk.zkOpers import Container_ZkOpers, Requests_ZkOpers
from containerCluster.baseContainerAction import ContainerCluster_Action_Base
from containerCluster.containerClusterCreateAction import ContainerCluster_create_Action
from componentProxy.componentContainerClusterValidator import ComponentContainerClusterValidator
from utils.threading_exception_queue import Threading_Exception_Queue
from common.abstractAsyncThread import Abstract_Async_Thread
from resource_letv.resource import Resource

from tornado.httpclient import AsyncHTTPClient
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from componentProxy.componentContainerModelFactory import ComponentContainerModelFactory
from componentProxy.componentContainerClusterConfigFactory import ComponentContainerClusterConfigFactory
from utils import handleTimeout, _get_property_dict, dispatch_mutil_task, _retrieve_userName_passwd, async_http_post
from utils.exceptions import CommonException


class ContainerCluster_Opers(Abstract_Container_Opers):
    
    component_container_cluster_validator = ComponentContainerClusterValidator()
    threading_exception_queue = Threading_Exception_Queue()
        
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, arg_dict):
        if not arg_dict.has_key('containerClusterName'):
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        if not arg_dict.has_key('networkMode'):
            raise UserVisiableException('params networkMode not be given, please check the params!')
        if not arg_dict.has_key('componentType'):
            raise UserVisiableException('params componentType not be given, please check the params!')
        
        _containerClusterName = arg_dict.get('containerClusterName')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(_containerClusterName)
        if exists:
            raise UserVisiableException('containerCluster %s has existed, choose another containerCluster name' % _containerClusterName)
        
        containerCluster_create_action = ContainerCluster_create_Action(arg_dict)
        containerCluster_create_action.start()

    def add(self, arg_dict):
        if not arg_dict.has_key('containerClusterName'):
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        if not arg_dict.has_key('nodeCount'):
            raise UserVisiableException('params nodeCount not be given, please check the params!')        
        if not arg_dict.has_key('networkMode'):
            raise UserVisiableException('params networkMode not be given, please check the params!')
        if not arg_dict.has_key('componentType'):
            raise UserVisiableException('params componentType not be given, please check the params!')
        
        cluster = arg_dict.get('containerClusterName')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if not exists:
            raise UserVisiableException('cluster %s not exist, you should give a existed cluster when add node to it!' % cluster)
        
        containerCluster_create_action = ContainerCluster_AddNode_Action(arg_dict)
        containerCluster_create_action.start()

    def remove(self, arg_dict):
        cluster = arg_dict.has_key('containerClusterName')
        if not cluster:
            raise UserVisiableException('params containerClusterName not be given, please check the params!')
        if not arg_dict.has_key('containerNameList'):
            raise UserVisiableException('params nodeCount not be given, please check the params!')
        
        zkOper = Container_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if not exists:
            raise UserVisiableException('containerCluster %s not existed, no need to remove' % cluster)
        
        containerCluster_remove_node_action = ContainerCluster_RemoveNode_Action(arg_dict)
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
                cluster_exist = self.__get_cluster_status(nodes)
                cluster.setdefault('status', cluster_exist)
                cluster.setdefault('clusterName', cluster_name)
                logging.info('sync action, cluster name:%s' % cluster)
                
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
        zkOper = Requests_ZkOpers()
        container_ip_list = zkOper.retrieve_container_list(containerClusterName)
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


class ContainerCluster_stop_Action(ContainerCluster_Action_Base):

    def __init__(self, containerClusterName):
        super(ContainerCluster_stop_Action, self).__init__(containerClusterName, 'stop')


class ContainerCluster_start_Action(ContainerCluster_Action_Base):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_start_Action, self).__init__(containerClusterName, 'start')


class ContainerCluster_destroy_Action(ContainerCluster_Action_Base):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_destroy_Action, self).__init__(containerClusterName, 'remove')


class ContainerCluster_AddNode_Action(Abstract_Async_Thread): 
    
    resource = Resource()
    
    component_manager_status_validator = ComponentManagerStatusValidator()
    
    component_container_model_factory = ComponentContainerModelFactory()
    
    component_container_cluster_config_factory = ComponentContainerClusterConfigFactory()
    
    component_container_cluster_validator = ComponentContainerClusterValidator()
    
    def __init__(self, arg_dict={}):
        super(ContainerCluster_AddNode_Action, self).__init__()
        self._arg_dict = arg_dict

    def run(self):
        __action_result = Status.failed
        __error_message = ''
        cluster = self._arg_dict.get('containerClusterName')
        node_count = self._arg_dict.get('nodeCount')
        try:
            logging.info('add node to cluster : %s' % cluster)
            __action_result = self.__issue_addNode_action(self._arg_dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            self.__update_zk_info_when_process_complete(cluster, __action_result, node_count, __error_message)

    def __issue_addNode_action(self, args={}):
        logging.info('args:%s' % str(args))
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        cluster = args.get('containerClusterName')
        
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        args.setdefault('component_config', _component_container_cluster_config)
        
        """
            need to get container_name from existing containers
        """
        
        host_ip_list_used, container_names = self.__get_containers_info_created(cluster)
        _component_container_cluster_config.exclude_servers = host_ip_list_used
        
        self.__update_add_node_info_to_zk(cluster, {'addResult' : Status.failed})
        
        """
            ---------------------------------  resource validate ---------------------------------------------  
        """
        is_res_verify = _component_container_cluster_config.is_res_verify
        if is_res_verify:
            self.resource.validateResource(_component_container_cluster_config)
        
        host_ip_list = self.resource.elect_servers(_component_container_cluster_config)
        
        logging.info('host_ip_list:%s' % str(host_ip_list))
        args.setdefault('host_ip_list', host_ip_list)
        
        ip_port_resource_list = self.resource.retrieve_ip_port_resource(host_ip_list, _component_container_cluster_config)
        args.setdefault('ip_port_resource_list', ip_port_resource_list)
        
        """
            ---------------------------------  get create container params--------------------------------------  
        """
        
        add_container_name_list = self.__get_add_containers_names(_component_container_cluster_config, container_names)
        _component_container_cluster_config.add_container_name_list = add_container_name_list
        
        logging.info('show args to get create containers args list: %s' % str(args))
        container_model_list = self.component_container_model_factory.create(args)

        """
            --------------------------------- dispatch create task and check --------------------------------------  
        """

        self.__dispatch_create_container_task(container_model_list)
        
        created = self.__check_node_added(_component_container_cluster_config)
        if not created:
            raise CommonException('cluster started failed, maybe part of nodes started, other failed!')
        
        _action_flag = True
        if _component_container_cluster_config.need_validate_manager_status:
            _action_flag = self.component_manager_status_validator.validate_manager_status_for_cluster(_component_type, container_model_list)
        
        logging.info('validator manager status result:%s' % str(_action_flag))
        _action_result = Status.failed if not _action_flag else Status.succeed
        return _action_result

    def __get_containers_info_created(self, cluster):
        host_ip_list, container_name_list = [], []
        zk_opers = Container_ZkOpers()
        container_list = zk_opers.retrieve_container_list(cluster)
        for container in container_list:
            container_value = zk_opers.retrieve_container_node_value(cluster, container)
            host_ip = container_value.get('hostIp')
            host_ip_list.append(host_ip)
            container_name = container_value.get('containerName')
            container_name_list.append(container_name)
        return host_ip_list, container_name_list

    def __get_add_containers_names(self, _component_container_cluster_config, container_names):
        add_container_name_list, container_number_list = [], []
        nodeCount = _component_container_cluster_config.nodeCount
        for container_name in container_names:
            container_prefix, container_number = re.findall('(.*-n-)(\d)', container_name)[0]
            container_number_list.append(int(container_number))
        max_number = max(container_number_list)
        if max_number < 5:
            max_number = 5
        for i in range(nodeCount):
            max_number += 1
            add_container_name = container_prefix + str(max_number)
            add_container_name_list.append(add_container_name)
        return add_container_name_list

    def __check_node_added(self, component_container_cluster_config):
        container_cluster_name = component_container_cluster_config.container_cluster_name
        nodeCount = component_container_cluster_config.nodeCount
        return handleTimeout(self.__is_node_started, (250, 2), container_cluster_name, nodeCount)

    def __is_node_started(self, container_cluster_name, nodeCount):
        
        """
            need to besure
        """
        
        zkOper = Container_ZkOpers()
        container_list = zkOper.retrieve_container_list(container_cluster_name)
        if len(container_list) != nodeCount:
            logging.info('container length:%s, nodeCount :%s' % (len(container_list), nodeCount) )
            return False
        status = self.component_container_cluster_validator.cluster_status_info(container_cluster_name)
        return status.get('status') == Status.started

    def __update_add_node_info_to_zk(self, cluster, add_result):
        zkOper = Container_ZkOpers()
        cluster_info = zkOper.retrieve_container_cluster_info(cluster)
        cluster_info.update(add_result)
        zkOper.write_container_cluster_info(cluster_info)

    def __dispatch_create_container_task(self, container_model_list):
        
        ip_port_params_list = []
        for container_model in container_model_list:
            property_dict = _get_property_dict(container_model)
            host_ip = property_dict.get('host_ip')
            ip_port_params_list.append((host_ip, options.port, property_dict))
        
        dispatch_mutil_task(ip_port_params_list, '/inner/container', 'POST')


class ContainerCluster_RemoveNode_Action(Abstract_Async_Thread):

    def __init__(self, args={}):
        super(ContainerCluster_AddNode_Action, self).__init__()
        self.args = args

    def run(self):
        try:
            self.__issue_remove_node_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_remove_node_action(self):
        params = self.__get_params()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        logging.info('params: %s' % str(params))
        
        async_client = AsyncHTTPClient()
        try:
            for host_ip, container_name_list in params.items():
                logging.info('container_name_list %s in host %s ' % (str(container_name_list), host_ip) )
                for container_name in container_name_list:
                    args = {'containerName':container_name}
                    request_uri = 'http://%s:%s/container/%s' % (host_ip, options.port)
                    logging.info('post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
                    async_http_post(async_client, request_uri, body=args, auth_username=adminUser, auth_password=adminPasswd)
        finally:
            async_client.close()
        
        if self.action == 'remove':
            self.__do_when_remove_cluster()

