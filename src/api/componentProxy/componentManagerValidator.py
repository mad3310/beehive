'''
Created on 2015-2-4

@author: asus
'''
from componentProxy.db.mysql.mysqlManagerValidator import MclusterManagerValidator
from componentProxy.loadbalance.gbalancer.gbalancerManagerValidator import GbalanceManagerValidator


class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''
    

    def __init__(self):
        '''
        Constructor
        '''
        
    def start_Status_Validator(self, _component_type, create_container_node_ip_list, container_model_list, num):
        _check_result = False
        if "mclusternode" == _component_type:
            manager_validator = MclusterManagerValidator()
        elif "mclustervip" == _component_type:
            manager_validator = GbalanceManagerValidator()
        else:
            manager_validator = None
            
        _check_result = manager_validator.validate_manager_status(create_container_node_ip_list, container_model_list, num)
        return _check_result
