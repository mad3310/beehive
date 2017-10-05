'''
Created on 2015-2-1

@author: asus
'''

from baseDockerModelCreator import BaseDockerModelCreator


class ComponentDockerModelFactory(object):
    '''
    classdocs
    '''
    base_docker_model_creator = BaseDockerModelCreator()

    def __init__(self):
        '''
        Constructor
        '''

    def create(self, arg_dict):
        docker_py_model = self.base_docker_model_creator.create(arg_dict)
        return docker_py_model