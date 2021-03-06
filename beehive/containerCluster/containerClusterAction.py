#!/usr/bin/env python
#-*- coding: utf-8 -*-


import sys
import logging

from status.status_enum import Status
from zk.zkOpers import Container_ZkOpers
from utils import handleTimeout
from utils.exceptions import CommonException
from containerCluster.baseContainerClusterAction import Base_ContainerCluster_Action, Base_ContainerCluster_create_Action
from componentProxy.componentContainerClusterConfigFactory import ComponentContainerClusterConfigFactory
from container.containerOpers import Container_Opers


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
    container_opers = Container_Opers()

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
        container_names = self.container_opers.generate_container_names(_component_type, node_count, _cluster)
        _component_container_cluster_config.container_names = container_names
        args.setdefault('component_config', _component_container_cluster_config)

        self.__create_cluser_info_to_zk(_network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_create_Action, self).create(args)

    def __create_cluser_info_to_zk(self, network_mode, component_type, component_container_cluster_config):
        containerCount = component_container_cluster_config.nodeCount
        containerClusterName = component_container_cluster_config.container_cluster_name
        use_ip = 'bridge' != network_mode

        _container_cluster_info = {
            'containerCount': containerCount,
            'containerClusterName': containerClusterName,
            'type': component_type,
            'isUseIp': use_ip
        }
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
            __action_result = self.add(self._arg_dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            self.update_zk_info_when_process_complete(cluster, __action_result, '')

    def add(self, args):
        logging.info('args:%s' % str(args))
        cluster = args.get('containerClusterName')
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        container_names = args.get('container_names')

        node_count = args.get('nodeCount')
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        _component_container_cluster_config.sum_count = self.__sum_count(cluster, node_count)

        exclude_servers = self.__exclude_servers(cluster)
        _component_container_cluster_config.exclude_servers = exclude_servers

        _component_container_cluster_config.container_names = container_names
        args.setdefault('component_config', _component_container_cluster_config)

        self.__update_cluser_info_to_zk(cluster, _network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_Add_Action, self).create(args)

    def __sum_count(self, cluster, node_count):
        zk_oper = Container_ZkOpers()
        cluster_info = zk_oper.retrieve_container_cluster_info(cluster)
        container_count = cluster_info.get('containerCount')
        return int(node_count) + int(container_count)

    def __exclude_servers(self, cluster):
        host_ip_list = []
        zk_opers = Container_ZkOpers()
        container_list = zk_opers.retrieve_container_list(cluster)
        for container in container_list:
            container_value = zk_opers.retrieve_container_node_value(cluster, container)
            host_ip = container_value.get('hostIp')
            host_ip_list.append(host_ip)
        return host_ip_list

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
        super(ContainerCluster_RemoveNode_Action, self).__init__(cluster, 'remove' , containers)

    def do_when_remove_cluster(self):

        def check():
            for container_node in self.container_nodes:
                container_status = zk_opers.retrieve_container_status_value(self.cluster, container_node)
                if container_status.get('status') != Status.destroyed:
                    return
            return True

        zk_opers = Container_ZkOpers()
        ret = handleTimeout(check, (50, 4))
        if not ret:
            raise CommonException('remove containers %s in containerCluster:%s failed' % (self.containers, self.cluster) )
        for container_node in self.container_nodes:
            logging.info('do delete container node :%s info in zookeeper' % container_node)
            zk_opers.delete_container_node(self.cluster, container_node)

        cluster_info = zk_opers.retrieve_container_cluster_info(self.cluster)
        node_count = cluster_info.get('containerCount')
        _node_count = int(node_count) - len(self.containers)
        cluster_info.update({'containerCount':_node_count})
        cluster_info.update({'start_flag':Status.succeed})
        zk_opers.write_container_cluster_info(cluster_info)
