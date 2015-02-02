'''
Created on 2015-2-1

@author: asus
'''
from common.componentProxy.db.mysql.mysqlDockerModelCreator import MysqlDockerModelCreator
from common.componentProxy.loadbalance.gbalancer.gbalancer.gbalancerDockerModelCreator import GbalancerDockerModelCreator

class ComponentDockerModelFactory(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def create(self, component_type, arg_dict):
        if 'mclusternode' == component_type:
            creator = MysqlDockerModelCreator()
            
        elif 'mclustervip' == component_type:
            creator = GbalancerDockerModelCreator()
    
        docker_py_model = creator.create(arg_dict)
        return docker_py_model