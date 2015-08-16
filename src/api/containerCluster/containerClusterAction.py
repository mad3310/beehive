import sys
import re
import logging

from componentProxy import _name
from status.status_enum import Status
from zk.zkOpers import Container_ZkOpers
from containerCluster.baseContainerClusterAction import Base_ContainerCluster_Action, Base_ContainerCluster_create_Action
from componentProxy.componentContainerClusterConfigFactory import ComponentContainerClusterConfigFactory


class ContainerCluster_stop_Action(Base_ContainerCluster_Action):

    def __init__(self, containerClusterName):
        super(ContainerCluster_stop_Action, self).__init__(containerClusterName, 'stop')


class ContainerCluster_start_Action(Base_ContainerCluster_Action):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_start_Action, self).__init__(containerClusterName, 'start')


class ContainerCluster_destroy_Action(Base_ContainerCluster_Action):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_destroy_Action, self).__init__(containerClusterName, 'remove')


class ContainerCluster_create_Action(Base_ContainerCluster_create_Action):

    component_container_cluster_config_factory = ComponentContainerClusterConfigFactory()

    def __init__(self, args):
        super(ContainerCluster_create_Action, self).__init__(args)
        self.args = args

    def run(self):
        __action_result = Status.failed
        __error_message = ''
        cluster = self.args.get('containerClusterName')
        try:
            logging.debug('begin create')
            __action_result = self.create(self.args)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            self.update_zk_info_when_process_complete(cluster, __action_result, __error_message)

    def create(self, args):
        logging.info('args:%s' % str(args))
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        _cluster = self.args.get('containerClusterName')

        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        node_count = _component_container_cluster_config.nodeCount
        _component_container_cluster_config.sum_count = node_count
        container_names = self.__get_container_names(_component_type, node_count, _cluster)
        _component_container_cluster_config.container_names = container_names
        args.setdefault('component_config', _component_container_cluster_config)
        
        self.__create_cluser_info_to_zk(_network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_create_Action, self).create(args)

    def __get_container_names(self, component_type, node_count, cluster):
        names = []
        mid_name = _name.get(component_type)
        for i in range(int(node_count)):
            container_name = 'd-%s-%s-n-%s' % (mid_name, cluster, str(i+1))
            names.append(container_name)
        return names

    def __create_cluser_info_to_zk(self, network_mode, component_type, component_container_cluster_config):
        containerCount = component_container_cluster_config.nodeCount
        containerClusterName = component_container_cluster_config.container_cluster_name
        
        _container_cluster_info = {}
        _container_cluster_info.setdefault('containerCount', containerCount)
        _container_cluster_info.setdefault('containerClusterName', containerClusterName)
        _container_cluster_info.setdefault('type', component_type)
        use_ip = True
        if 'bridge' == network_mode:
            use_ip = False
        _container_cluster_info.setdefault('isUseIp', use_ip)
        zkOper = Container_ZkOpers()
        zkOper.write_container_cluster_info(_container_cluster_info)


class ContainerCluster_Add_Action(Base_ContainerCluster_create_Action):

    component_container_cluster_config_factory = ComponentContainerClusterConfigFactory()

    def __init__(self, args):
        super(ContainerCluster_Add_Action, self).__init__(args)
        self.args = args

    def run(self):
        cluster = self._arg_dict.get('containerClusterName')
        try:
            logging.debug('begin to add containers')
            __action_result = self.create(self._arg_dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            self.update_zk_info_when_process_complete(cluster, __action_result, '')

    def create(self, args):
        logging.info('args:%s' % str(args))
        cluster = args.get('containerClusterName')
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        
        node_count = args.get('nodeCount')
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        _component_container_cluster_config.sum_count = self.__sum_count(cluster, node_count)
        
        host_ip_list_used, container_names = self.__get_containers_info_created(cluster)
        _component_container_cluster_config.exclude_servers = host_ip_list_used
        
        container_names = self.__get_container_names(_component_container_cluster_config, container_names)
        _component_container_cluster_config.container_names = container_names
        args.setdefault('component_config', _component_container_cluster_config)
        
        self.__update_cluser_info_to_zk(cluster, _network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_Add_Action, self).create(args)

    def __sum_count(self, cluster, node_count):
        zk_oper = Container_ZkOpers()
        cluster_info = zk_oper.retrieve_container_cluster_info(cluster)
        container_count = cluster_info.get('containerCount')
        return int(node_count) + int(container_count)        

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

    def __get_container_names(self, _component_container_cluster_config, container_names):
        add_container_name_list, container_number_list = [], []
        nodeCount = _component_container_cluster_config.nodeCount
        for container_name in container_names:
            container_prefix, container_number = re.findall('(.*-n-)(\d)', container_name)[0]
            container_number_list.append(int(container_number))
        max_number = max(container_number_list)
        if max_number < 4:
            max_number = 4
        for i in range(nodeCount):
            max_number += 1
            add_container_name = container_prefix + str(max_number)
            add_container_name_list.append(add_container_name)
        return add_container_name_list

    def __update_cluser_info_to_zk(self, cluster, network_mode, component_type, component_container_cluster_config):
        sum_count = component_container_cluster_config.sum_count
        
        _container_cluster_info = {}
        _container_cluster_info.setdefault('containerClusterName', cluster)
        _container_cluster_info.setdefault('containerCount', sum_count)
        _container_cluster_info.setdefault('start_flag', Status.failed)
        
        zkOper = Container_ZkOpers()
        zkOper.write_container_cluster_info(_container_cluster_info)


class ContainerCluster_RemoveNode_Action(Base_ContainerCluster_Action):

    def __init__(self, cluster, containers):
        super(ContainerCluster_RemoveNode_Action, self).__init__(cluster, containers, 'remove')
    
#     def do_when_remove_cluster(self):
#         super(ContainerCluster_RemoveNode_Action, self).do_when_remove_cluster()
#         zk_opers = Container_ZkOpers()
#         for container_node in self.container_nodes:
#             zk_opers.delete_container_node(self.cluster, container_node)
#         
#         cluster_info = zk_opers.retrieve_container_cluster_info(self.cluster)
#         node_count = cluster_info.get('containerCount')
#         _node_count = int(node_count) - len(self.containers)
#         cluster_info.update({'containerCount':_node_count})
#         zk_opers.write_container_cluster_info(cluster_info)

#     def run(self):
#         try:
#             self.__issue_remove_node_action()
#         except:
#             self.threading_exception_queue.put(sys.exc_info())
# 
#     def __issue_remove_node_action(self):
#         
#         cluster = self.args.get('containerClusterName')
#         _container_name_list = self.args.get('containerNameList')
#         container_name_list = _container_name_list.split(',')
#         zkOper = Container_ZkOpers()
#         adminUser, adminPasswd = _retrieve_userName_passwd()
#         async_client = AsyncHTTPClient()
#         
#         try:
#             for container_name in container_name_list:
#                 container_node = self.container_opers.get_container_node_from_container_name(cluster, container_name)
#                 container_node_value = zkOper.retrieve_container_node_value(cluster, container_node)
#                 host_ip = container_node_value.get('hostIp')
#                 args = {'containerName':container_name}
#                 request_uri = 'http://%s:%s/container/remove' % (host_ip, options.port)
#                 logging.info('remove node action-----  url: %s, \n container name: %s' % ( request_uri, container_name ) )
#                 async_http_post(async_client, request_uri, body=args, auth_username=adminUser, auth_password=adminPasswd)
#         finally:
#             async_client.close()