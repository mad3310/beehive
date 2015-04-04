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
        config = importlib.import_module('%s.%s.%sContainerClusterConfig.%sContainerClusterConfig'%(_component_path, 
                                                                                                    _component_type, 
                                                                                                    _component_type, 
                                                                                                    _component_type)) 
        return config
