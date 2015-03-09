'''
Created on 2015-2-4

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerClusterValidator import MysqlContainerClusterValidator
from componentProxy.loadbalance.gbalancer.gbalancerContainerClusterValidator import GbalancerContainerClusterValidator
from componentProxy.webcontainer.nginx.nginxContainerClusterValidator import NginxContainerClusterValidator


class ComponentContainerClusterValidator(object):
    '''
    classdocs
    '''
    

    def __init__(self):
        '''
        Constructor
        '''
        
    def container_cluster_status_validator(self, _component_type, container_cluster_name):
        _check_result = False
        if "mclusternode" == _component_type:
            container_cluster_validator = MysqlContainerClusterValidator()
        elif "mclustervip" == _component_type:
            container_cluster_validator = GbalancerContainerClusterValidator()
        elif 'nginx' == _component_type:
            container_cluster_validator = NginxContainerClusterValidator()
        else:
            container_cluster_validator = None
            
        _check_result = container_cluster_validator.validate_container_cluster_status(container_cluster_name)
        return _check_result
