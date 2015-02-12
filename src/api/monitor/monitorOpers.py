#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

from resource_letv.statusOpers import CheckContainersUnderOom, CheckResIpUsable, CheckResIpNum 

import logging

'''
@todo: need to remove? no reference.
'''
class ResInfoSyncHandler:    
    
    def retrieve_info(self, data_node_info_list):
        return self._action(data_node_info_list)
        
    def _action(self, data_node_info_list):
        logging.info("_retrieve_db_info_sync:do nothing!")

class ContainerInfoAsyncHandler:
    """monitor container item
    
    """
    
    #check_cons_mem_load = CheckContainersMemLoad()
    check_cons_under_oom = CheckContainersUnderOom()
    
    def retrieve_info(self):
        self.check_cons_under_oom.check()


class ResInfoAsyncHandler:
    """monitor resource item
    
    """
    
    check_res_ip_usable = CheckResIpUsable()
    check_res_ip_num = CheckResIpNum()
    
    '''
    @todo: 
    1. the rest value of disk
    2. the rest value of memory
    '''
    
    def retrieve_info(self):
        self.check_res_ip_usable.check()
        self.check_res_ip_num.check()
