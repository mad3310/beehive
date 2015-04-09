'''
Created on 2015-2-1

@author: asus
'''

from componentProxy import _path
import importlib


class ComponentContainerModelFactory(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def create(self, args={}):
        _component_type = args.get('componentType')
        _component_path = _path.get(_component_type)

        module_path = '%s.%s.%sContainerModelCreator' % (_component_path, _component_type, _component_type)
        
        cls_name = '%sContainerModelCreator' % _component_type.capitalize()
        
        module_obj = importlib.import_module(module_path)
        creator = getattr(module_obj, cls_name)(args)
        
        _arg_list = creator.create(args)
        return _arg_list
