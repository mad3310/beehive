'''
Created on 2015-2-1

@author: asus
'''
#-*- coding: utf-8 -*-
from abc import abstractmethod

class AbstractDockerModelCreator(object):
    '''
    classdocs
    '''


    @abstractmethod
    def create(self, arg_dict):
        raise NotImplementedError, "Cannot call abstract method"
        