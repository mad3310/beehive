#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

from statusOpers import CheckContainersUnderOom, CheckResIpNum, CheckContainersOomKillDisable, CheckServerPortNum


class ContainerResCheckHandler:
    """monitor container item
    
    """
    
    check_cons_oom_kill_disable = CheckContainersOomKillDisable()
    check_cons_under_oom = CheckContainersUnderOom()
    
    def retrieve_info(self):
        self.check_cons_under_oom.check()
        self.check_cons_oom_kill_disable.check()


class ServerResCheckcHandler:
    """monitor resource item
    
    """
    
    check_res_ip_num = CheckResIpNum()
    check_server_port_num = CheckServerPortNum()
    
    '''
    @todo:
    1. the rest value of disk
    2. the rest value of memory
    '''
    
    def retrieve_info(self):
        self.check_res_ip_num.check()
        self.check_server_port_num.check()