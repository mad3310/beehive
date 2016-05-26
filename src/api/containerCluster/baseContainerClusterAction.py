'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys

from tornado.options import options
from tornado.httpclient import AsyncHTTPClient
from common.abstractAsyncThread import Abstract_Async_Thread
from utils import async_http_post, _retrieve_userName_passwd, getNIC
from zk.zkOpers import Container_ZkOpers
from resource_letv.resource import Resource
from utils import handleTimeout, _get_property_dict, dispatch_mutil_task
from utils.exceptions import CommonException
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from componentProxy.componentContainerClusterValidator import ComponentContainerClusterValidator
from status.status_enum import Status
from componentProxy.baseContainerModelCreator import BaseContainerModelCreator
from container.containerOpers import Container_Opers


class Base_ContainerCluster_Action(Abstract_Async_Thread):
    """if param "containers" not given, the action is about cluster;

    if param "containers" are given, the action is about such containers.
    """

    container_opers = Container_Opers()

    def __init__(self, containerClusterName, action, containers=None):
        super(Base_ContainerCluster_Action, self).__init__()
        self.cluster = containerClusterName
        self.action = action
        self.containers = containers

    def run(self):
        try:
            self.__issue_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_action(self):
        params = self.__get_params()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        logging.info('params: %s' % str(params))

        async_client = AsyncHTTPClient()
        try:
            for host_ip, container_name_list in params.items():
                logging.info('container_name_list %s in host %s ' % (str(container_name_list), host_ip) )
                for container_name in container_name_list:
                    args = {'containerName':container_name}
                    request_uri = 'http://%s:%s/container/%s' % (host_ip, options.port, self.action)
                    logging.info('post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
                    async_http_post(async_client, request_uri, body=args, auth_username=adminUser, auth_password=adminPasswd)
        finally:
            async_client.close()

        if self.action == 'remove':
            self.do_when_remove_cluster()

    def do_when_remove_cluster(self):
        zkOper = Container_ZkOpers()
        cluster_info = zkOper.retrieve_container_cluster_info(self.cluster)
        use_ip = cluster_info.get('isUseIp')
        if use_ip:
            container_ip_list = zkOper.retrieve_container_list(self.cluster)
            logging.info('container_ip_list:%s' % str(container_ip_list) )
            zkOper.recover_ips_to_pool(container_ip_list)

    def __get_params(self):
        """
            two containers may be with a host_ip
        """

        params, container_info, container_nodes = {}, {}, []

        zkOper = Container_ZkOpers()
        if self.containers:
            for container in self.containers:
                container_node = self.container_opers.get_container_node_from_container_name(self.cluster, container)
                container_nodes.append(container_node)
        else:
            container_nodes = zkOper.retrieve_container_list(self.cluster)
        self.container_nodes = container_nodes
        for container_node in self.container_nodes:
            container_name_list = []
            container_info = zkOper.retrieve_container_node_value(self.cluster, container_node)
            container_name = container_info.get('containerName')
            host_ip = container_info.get('hostIp')
            container_name_list.append(container_name)
            if host_ip in params:
                container_name_list.extend(params[host_ip])
            params[host_ip] = container_name_list
        return params


class Base_ContainerCluster_create_Action(Abstract_Async_Thread):

    resource = Resource()

    component_manager_status_validator = ComponentManagerStatusValidator()

    component_container_cluster_validator = ComponentContainerClusterValidator()

    base_container_model_creator = BaseContainerModelCreator()

    def __init__(self, arg_dict={}):
        super(Base_ContainerCluster_create_Action, self).__init__()
        self._arg_dict = arg_dict

    def run(self):
        raise NotImplementedError()

    def create(self, args={}):
        logging.info('args:%s' % str(args))

        _component_type = args.get('componentType')
        cluster = args.get('containerClusterName')
        logging.info('component_type : %s' % str(_component_type))
        logging.info('containerClusterName : %s' % cluster)

        _component_container_cluster_config = args.get('component_config')

        """
            ---------------------------------  resource validate ---------------------------------------------
        """

        is_res_verify = _component_container_cluster_config.is_res_verify
        if is_res_verify:
            self.resource.validateResource(_component_container_cluster_config)

        host_ip_list = self.resource.elect_servers(_component_container_cluster_config)

        logging.info('host_ip_list:%s' % str(host_ip_list))
        args.setdefault('host_ip_list', host_ip_list)

        NIC = self.retrieve_cluster_NIC()
        args.setdefault('NIC', NIC)

        ip_port_resource_list = self.resource.retrieve_ip_port_resource(host_ip_list, _component_container_cluster_config)
        args.setdefault('ip_port_resource_list', ip_port_resource_list)

        """
            ---------------------------------  get create container params--------------------------------------
        """

        logging.info('show args to get create containers args list: %s' % str(args))
        container_model_list = self.base_container_model_creator.create(args)

        """
            ---------------------------- dispatch creating task and check the result----------------------------
        """

        self.__dispatch_create_container_task(container_model_list)

        created = self.__check_containers_started(_component_container_cluster_config)
        if not created:
            raise CommonException('cluster started failed, maybe part of nodes started, other failed!')

        _action_flag = True
        if _component_container_cluster_config.need_validate_manager_status:
            _action_flag = self.component_manager_status_validator.validate_manager_status_for_cluster(_component_type, container_model_list)

        logging.info('validator manager status result:%s' % str(_action_flag))
        _action_result = Status.failed if not _action_flag else Status.succeed
        return _action_result

    def retrieve_cluster_NIC(self):
        zkOper = Container_ZkOpers()
        uuid = zkOper.getClusterUUID()
        uuid_info = zkOper.retrieve_uuid_info(uuid)
        NIC = uuid_info.get('NIC')
        if not NIC:
            NIC = getNIC()
            uuid_info.update({'NIC': NIC})
            zkOper.writeClusterInfo(uuid, uuid_info)
        return NIC

    def __dispatch_create_container_task(self, container_model_list):

        ip_port_params_list = []
        for container_model in container_model_list:
            property_dict = _get_property_dict(container_model)
            host_ip = property_dict.get('host_ip')
            ip_port_params_list.append((host_ip, options.port, property_dict))

        dispatch_mutil_task(ip_port_params_list, '/inner/container', 'POST')

    def __check_containers_started(self, component_container_cluster_config):

        container_cluster_name = component_container_cluster_config.container_cluster_name
        sum_count = component_container_cluster_config.sum_count
        return handleTimeout(self.__is_containers_started, (250, 4), container_cluster_name, sum_count)

    def __is_containers_started(self, container_cluster_name, sum_count):

        zkOper = Container_ZkOpers()
        container_list = zkOper.retrieve_container_list(container_cluster_name)
        if len(container_list) != sum_count:
            logging.info('container length:%s, sum_count :%s' % (len(container_list), sum_count) )
            return False
        logging.info('sum_count is created: %s' % sum_count)
        status = self.component_container_cluster_validator.container_cluster_status_validator(container_cluster_name)
        logging.info('cluster status: %s' % status)
        return status.get('status') == Status.started

    def update_zk_info_when_process_complete(self, cluster, create_result='failed', error_msg=''):

        zkOper = Container_ZkOpers()
        _container_cluster_info = zkOper.retrieve_container_cluster_info(cluster)
        _container_cluster_info['start_flag']=create_result
        _container_cluster_info['error_msg']=error_msg
        _container_cluster_info['containerClusterName']=cluster
        zkOper.write_container_cluster_info(_container_cluster_info)
