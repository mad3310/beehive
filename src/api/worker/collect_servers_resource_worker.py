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