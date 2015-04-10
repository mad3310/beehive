#!/usr/bin/env python2.6.6
#coding:utf-8



import sys

from common.abstractAsyncThread import Abstract_Async_Thread
from server.serverOpers import Server_Opers


class Collect_Servers_Resource_Worker(Abstract_Async_Thread):
    
    server_opers = Server_Opers()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Collect_Servers_Resource_Worker,self).__init__()

    def run(self):
        
        try:
            self.server_opers.write_host_resource_to_zk()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())

# import logging
# import kazoo
# from zk.zkOpers import ZkOpers
# from zk.zkOpers import ZkOpers
# 
#     def run(self):
#         isLock, lock = False, None
#          
#         zkOper = ZkOpers()
#         try:
#             isLock, lock = zkOper.lock_collect_resource_action()
#         except kazoo.exceptions.LockTimeout:
#             logging.info("a thread is running on collect resource, give up this operation on this machine!")
#             return
#          
#         if not isLock:
#             return
#          
#         try:
#             self.__action_collect_servers_resource()
#         except Exception:
#             self.threading_exception_queue.put(sys.exc_info())
#         finally:
#             if isLock:
#                 zkOper.unLock_collect_resource_action(lock)
#                  
#             zkOper.close()
