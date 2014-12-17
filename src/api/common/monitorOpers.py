#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

from statusOpers import *

import logging


class ResInfoSyncHandler:    
    
    def retrieve_info(self, data_node_info_list):
        return self._action(data_node_info_list)
        
    def _action(self, data_node_info_list):
        logging.info("_retrieve_db_info_sync:do nothing!")


class ContainerInfoAsyncHandler:
    """monitor container item
    
    """
    
    check_res_mem_load = CheckResMemLoad()
    
    def retrieve_info(self):
        self._action()
    
    def _action(self):
        self.check_res_mem_load.check()


class ResInfoAsyncHandler:
    """monitor resource item
    
    """
    
    check_res_ip_usable = CheckResIpUsable()
    check_res_ip_num = CheckResIpNum()
    
    def __init__(self):
        pass
    
    def retrieve_info(self):
        self._action()
    
    def _action(self):
        self.check_res_ip_usable.check()
        self.check_res_ip_num.check()
