'''
Created on 2015-2-4

@author: asus
'''
import logging
from status.status_enum import Status
from componentProxy.db.mysql.mysqlContainerClusterValidator import MysqlContainerClusterValidator
from componentProxy.loadbalance.gbalancer.gbalancerContainerClusterValidator import GbalancerContainerClusterValidator
from componentProxy.webcontainer.nginx.nginxContainerClusterValidator import NginxContainerClusterValidator
from componentProxy.webcontainer.jetty.jettyContainerClusterValidator import JettyContainerClusterValidator


class ComponentContainerClusterValidator(object):
    '''
    classdocs
    '''
    

    def __init__(self):
        '''
        Constructor
        '''
        
#     def container_cluster_status_validator(self, _component_type, container_cluster_name):
#         _check_result = False
#         if "mclusternode" == _component_type:
#             container_cluster_validator = MysqlContainerClusterValidator()
#         elif "mclustervip" == _component_type:
#             container_cluster_validator = GbalancerContainerClusterValidator()
#         elif 'nginx' == _component_type:
#             container_cluster_validator = NginxContainerClusterValidator()
#         elif 'jetty' == _component_type:
#             container_cluster_validator = JettyContainerClusterValidator()
#         else:
#             container_cluster_validator = None
#             
#         _check_result = container_cluster_validator.validate_container_cluster_status(container_cluster_name)
#         return _check_result

    def container_cluster_status_validator(self, _component_type, cluster):
        
        container_ip_list = self.zk_oper.retrieve_container_list(cluster)
        status_list, cluster_status = [], {}
        for container_ip in container_ip_list:
            status = self.zk_oper.retrieve_container_status_value(cluster, container_ip)
            status_list.append(status.get('status'))
        
        ret = self.__get_cluster_status(status_list)
        cluster_status.setdefault('status', ret)
        if ret == Status.destroyed:
            logging.info('delete containerCluster: %s' % cluster)
            self.zk_oper.delete_container_cluster(cluster)
        return cluster_status

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