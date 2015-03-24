'''
Created on 2015-2-5

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerClusterConfig import MysqlContainerClusterConfig
from componentProxy.loadbalance.gbalancer.gbalancerContainerClusterConfig import GbalancerContainerClusterConfig
from componentProxy.webcontainer.nginx.nginxContainerClusterConfig import NginxContainerClusterConfig
from componentProxy.webcontainer.jetty.jettyContainerClusterConfig import JettyContainerClusterConfig


class ComponentContainerClusterConfigFactory(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    def retrieve_config(self, args):
        config = None
        _component_type = args.get('componentType')
        if "mclustervip" == _component_type:
            config = GbalancerContainerClusterConfig(args)
        elif "mclusternode" == _component_type:
            config = MysqlContainerClusterConfig(args)
        elif "nginx" == _component_type:
            config = NginxContainerClusterConfig(args)
        elif "jetty" == _component_type:
            config = JettyContainerClusterConfig(args)
        else:
            pass
            
        return config