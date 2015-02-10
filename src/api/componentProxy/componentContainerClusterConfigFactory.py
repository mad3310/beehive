'''
Created on 2015-2-5

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerClusterConfig import MysqlContainerClusterConfig
from componentProxy.loadbalance.gbalancer.gbalancerContainerClusterConfig import GbalancerContainerClusterConfig

class ComponentContainerClusterConfigFactory(object):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        
    def retrieve_config(self, args):
        _component_type = args.get('componentType')
        if "mclustervip" == _component_type:
            config = GbalancerContainerClusterConfig(args)
        elif "mclusternode" == _component_type:
            config = MysqlContainerClusterConfig(args)
        
        return config