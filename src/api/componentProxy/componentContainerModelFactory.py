'''
Created on 2015-2-1

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerModelCreator import MySQLContainerModelCreator
from componentProxy.loadbalance.gbalancer.gbalancerContainerModelCreator import GbalancerContainerModelCreator

class ComponentContainerModelFactory(object):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
    
    def create(self, _component_type, arg_dict, containerCount, containerClusterName):
        if "mclustervip" == _component_type:
            creator = GbalancerContainerModelCreator()
        elif "mclusternode" == _component_type:
            creator = MySQLContainerModelCreator()
        
        _arg_list = creator.create(arg_dict, containerCount, containerClusterName)
        return _arg_list