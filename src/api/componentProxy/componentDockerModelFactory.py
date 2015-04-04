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
        creator = importlib.import_module('%s.%s.%sDockerModelCreator.%sDockerModelCreator'%(_component_path, 
                                                                                             component_type, 
                                                                                             component_type, 
                                                                                             component_type)) 
        docker_py_model = creator.create(arg_dict)
        return docker_py_model
