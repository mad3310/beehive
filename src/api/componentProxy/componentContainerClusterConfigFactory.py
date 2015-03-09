'''
Created on 2015-2-5

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerClusterConfig import MysqlContainerClusterConfig
from componentProxy.loadbalance.gbalancer.gbalancerContainerClusterConfig import GbalancerContainerClusterConfig
from componentProxy.webcontainer.nginx.nginxContainerClusterConfig import NginxContainerClusterConfig

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
        elif "mclusternode" == _component_type:
            config = NginxContainerClusterConfig(args)
        else:
            pass
            
        return config