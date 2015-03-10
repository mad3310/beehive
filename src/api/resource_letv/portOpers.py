'''
Created on 2015-2-8

@author: asus
'''
import logging

class PortOpers(object):
    '''
    classdocs
    '''
    
    def retrieve_port_resource(self, host_ip_list, every_host_port_count=1):
        port_list = [38080]
        return port_list
#         port_dict = {}
#         isLock,lock = self.zkOper.lock_assign_port()
#         try:
#             if isLock:
#                 for host_ip in host_ip_list:
#                     port_dict.setdefault(self.zkOper.retrieve_port(host_ip, every_host_port_count))
#         finally:
#             if isLock:
#                 self.zkOper.unLock_assign_port(lock)
#         return port_dict
        