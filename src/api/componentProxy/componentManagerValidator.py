'''
Created on 2015-2-4

@author: asus
'''
from componentProxy.db.mysql.mclusterOper import MclusterManager

class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''
    

    def __init__(self):
        '''
        Constructor
        '''
        
    def start_Status_Validator(self, _component_type, create_container_node_ip_list, create_container_arg_list, num):
        _check_result = False
        if "mclusternode" == _component_type:
            _managerOpers = MclusterManager()
        elif "mclustervip" == _component_type:
            _managerOpers = None
        else:
            _managerOpers = None
            
        _check_result = self._managerOpers.validate_manager_status(create_container_node_ip_list, create_container_arg_list, num)
        return _check_result
            