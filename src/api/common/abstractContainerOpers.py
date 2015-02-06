#-*- coding: utf-8 -*-
from abc import abstractmethod
from zk.zkOpers import ZkOpers

'''
Created on 2013-7-21

@author: asus
'''

class Abstract_Container_Opers(object):
    
    zkOper = ZkOpers('127.0.0.1', 2181)
    
    @abstractmethod
    def create(self, arg_dict):
        raise NotImplementedError, "Cannot call abstract method"
    
    @abstractmethod
    def start(self, arg_dict):
        raise NotImplementedError, "Cannot call abstract method"

    @abstractmethod
    def stop(self, arg_dict):
        raise NotImplementedError, "Cannot call abstract method"
    
    @abstractmethod
    def destroy(self, arg_dict):
        raise NotImplementedError, "Cannot call abstract method"
    
