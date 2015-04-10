#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

from statusOpers import CheckContainersUnderOom, CheckResIpNum 


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
    
    check_res_ip_num = CheckResIpNum()
        
    '''
    @todo: 
    1. the rest value of disk
    2. the rest value of memory
    '''
    def retrieve_info(self):
        self.check_res_ip_num.check()
