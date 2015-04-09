'''
Created on 2015-2-1

@author: asus
'''

import importlib

from componentProxy import _path


class ComponentDockerModelFactory(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
    
    def create(self, component_type, arg_dict):
        _component_path = _path.get(component_type)

        module_path = '%s.%s.%sDockerModelCreator' % (_component_path, component_type, component_type)
        
        cls_name = '%sDockerModelCreator' % component_type.capitalize()
        
        module_obj = importlib.import_module(module_path)
        creator = getattr(module_obj, cls_name)()
        
        docker_py_model = creator.create(arg_dict)
        return docker_py_model
