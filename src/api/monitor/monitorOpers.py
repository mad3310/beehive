#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

from statusOpers import CheckContainersUnderOom, CheckResIpUsable, CheckResIpNum 


class ContainerInfoAsyncHandler:
    """monitor container item
    
    """
    '''
    @todo
        container memory
        container cpuacct
        container networkio
    '''
    
    #check_cons_mem_load = CheckContainersMemLoad()
    check_cons_under_oom = CheckContainersUnderOom()
    
    def retrieve_info(self):
        self.check_cons_under_oom.check()
        self.check_cons_mem_load.check()

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
