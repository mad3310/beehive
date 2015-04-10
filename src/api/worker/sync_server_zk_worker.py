#!/usr/bin/env python2.6.6
#coding:utf-8

import sys
import logging
import kazoo

from zk.zkOpers import ZkOpers
from common.abstractAsyncThread import Abstract_Async_Thread
from serverCluster.serverClusterOpers import ServerCluster_Opers


class Sync_Server_Zk_Worker(Abstract_Async_Thread):
    
    serverCluster_opers = ServerCluster_Opers()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Sync_Server_Zk_Worker, self).__init__()

    def run(self):
        isLock, lock = False, None
          
        zkOper = ZkOpers()
        try:
            isLock, lock = zkOper.lock_collect_resource_action()
        except kazoo.exceptions.LockTimeout:
            logging.info("a thread is running on collect resource, give up this operation on this machine!")
            return
          
        if not isLock:
            return
        
        try:
            self.serverCluster_opers.Update()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            if isLock:
                zkOper.unLock_collect_resource_action(lock)
                  
            zkOper.close()