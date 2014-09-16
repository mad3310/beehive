#-*- coding: utf-8 -*-
from abc import abstractmethod
from common.zkOpers import ZkOpers

'''
Created on 2013-7-21

@author: asus
'''

class Abstract_Container_Opers(object):
    
    zkOper = ZkOpers('127.0.0.1',2181)
    
    @abstractmethod
    def create(self, dict):
        raise NotImplementedError, "Cannot call abstract method"
    
    @abstractmethod
    def destory(self):
        raise NotImplementedError, "Cannot call abstract method"
    
