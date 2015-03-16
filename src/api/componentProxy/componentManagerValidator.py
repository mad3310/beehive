'''
Created on 2015-2-4

@author: asus
'''
from componentProxy.db.mysql.mysqlManagerValidator import MclusterManagerValidator
from componentProxy.loadbalance.gbalancer.gbalancerManagerValidator import GbalanceManagerValidator
from componentProxy.webcontainer.nginx.nginxManagerValidator import NginxManagerValidator


class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
    '''
    @todo: study the importlib way to replace if else, even if condition is limit, use dict way to replace it
    '''    
    def start_Status_Validator(self, _component_type, container_model_list, num):
        _check_result = False
        if "mclusternode" == _component_type:
            manager_validator = MclusterManagerValidator(container_model_list)
        elif "mclustervip" == _component_type:
            manager_validator = GbalanceManagerValidator(container_model_list)
        elif "nginx" == _component_type:
            manager_validator = NginxManagerValidator(container_model_list)
        else:
            manager_validator = None
            
        _check_result = manager_validator.validate_manager_status(num)
        return _check_result
