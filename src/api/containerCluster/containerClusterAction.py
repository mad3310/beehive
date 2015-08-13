import sys
import logging

from status.status_enum import Status
from zk.zkOpers import Container_ZkOpers
from containerCluster.baseContainerClusterAction import Base_ContainerCluster_Action, Base_ContainerCluster_create_Action


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
        _component_container_cluster_config = args.get('component_config')
        self.__create_container_cluser_info_to_zk(_network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_create_Action, self).create(args)

    def __create_container_cluser_info_to_zk(self, network_mode, component_type, component_container_cluster_config):
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

    def __init__(self):
        super(ContainerCluster_Add_Action, self).__init__()

    def run(self):
        cluster = self._arg_dict.get('containerClusterName')
        try:
            logging.debug('begin create')
            __action_result = self.create(self._arg_dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            self.update_zk_info_when_process_complete(cluster, __action_result, '')

    def create(self, args):
        logging.info('args:%s' % str(args))
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        _component_container_cluster_config = args.get('component_config')
        self.__create_container_cluser_info_to_zk(_network_mode, _component_type, _component_container_cluster_config)
        return super(ContainerCluster_create_Action, self).create(args)

