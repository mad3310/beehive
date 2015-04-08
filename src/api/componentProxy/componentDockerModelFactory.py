'''
Created on 2015-2-1

@author: asus
'''
from componentProxy.db.mysql.mysqlDockerModelCreator import MysqlDockerModelCreator
from componentProxy.loadbalance.gbalancer.gbalancerDockerModelCreator import GbalancerDockerModelCreator
from componentProxy.webcontainer.nginx.nginxDockerModelCreator import NginxDockerModelCreator
from componentProxy.webcontainer.jetty.jettyDockerModelCreator import JettyDockerModelCreator
from componentProxy.store.cbase.cbaseDockerModelCreator import CbaseDockerModelCreator
from componentProxy.loadbalance.mclustervip.mclustervipDockerModelCreator import MclustervipDockerModelCreator


class ComponentDockerModelFactory(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
    
    def create(self, _component_type, arg_dict):
        if 'mclusternode' == _component_type:
            creator = MysqlDockerModelCreator()

        elif 'mclustervip' == _component_type:
            creator = MclustervipDockerModelCreator()
            
        elif 'gbalancer' == _component_type:
            creator = GbalancerDockerModelCreator()
        
        elif 'nginx' == _component_type:
            creator = NginxDockerModelCreator()
        
        elif 'jetty' == _component_type:
            creator = JettyDockerModelCreator()

        elif 'cbase' == _component_type:
            creator = CbaseDockerModelCreator()

        else:
            pass
            
        docker_py_model = creator.create(arg_dict)
        return docker_py_model