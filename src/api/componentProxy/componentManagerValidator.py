'''
Created on 2015-2-4

@author: asus
'''

import importlib

from componentProxy import _path

class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

    def start_status_validator(self, component_type, container_name):
        _check_result = False
        _component_path = _path.get('_component_type')
        manager_validator = importlib.import_module('%s.%s.%sOper.%sManager'%(_component_path, 
                                                                              component_type, 
                                                                              component_type, 
                                                                              component_type)) 
        _check_result = manager_validator.manager_status(container_name)
        return _check_result
