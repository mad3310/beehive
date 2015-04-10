#!/usr/bin/env python2.6.6
#coding:utf-8

import sys

from common.abstractAsyncThread import Abstract_Async_Thread
from serverCluster.serverClusterOpers import ServerCluster_Opers


class Sync_Server_Zk_Worker(Abstract_Async_Thread):
    
    serverCluster_opers = ServerCluster_Opers()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Sync_Server_Zk_Worker, self).__init__()

    def run(self):
        
        try:
            self.serverCluster_opers.Update()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())