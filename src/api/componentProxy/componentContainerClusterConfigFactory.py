'''
Created on 2015-2-5

@author: asus
'''

import importlib

from componentProxy import _path


class ComponentContainerClusterConfigFactory(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    def retrieve_config(self, args):
        _component_type = args.get('componentType')
        _component_path = _path.get(_component_type)
        module_path = '%s.%s.%sContainerClusterConfig' % (_component_path, _component_type, _component_type)
        
        cls_name = '%sContainerClusterConfig' % _component_type.capitalize()
        
        module_obj = importlib.import_module(module_path)
        config = getattr(module_obj, cls_name)(args)
        return config
