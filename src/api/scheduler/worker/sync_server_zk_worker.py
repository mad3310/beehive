#!/usr/bin/env python2.6.6
#coding:utf-8

import sys
import logging
import kazoo

from zk.zkOpers import Scheduler_ZkOpers
from common.abstractAsyncThread import Abstract_Async_Thread
from serverCluster.serverClusterOpers import ServerCluster_Opers


class Sync_Server_Zk_Worker(Abstract_Async_Thread):
    
    serverCluster_opers = ServerCluster_Opers()
    
    def __init__(self):
        super(Sync_Server_Zk_Worker, self).__init__()

    def run(self):
        isLock, lock = False, None
        logging.info('do sync server')
        zkOper = Scheduler_ZkOpers()
        try:
            isLock, lock = zkOper.lock_sync_server_zk_action()
        except kazoo.exceptions.LockTimeout:
            logging.info("a thread is running on collect resource, give up this operation on this machine!")
            return
        
        if not isLock:
            return
        
        try:
            cluster_list = zkOper.retrieve_cluster_list()
            if not cluster_list:
                logging.info('no cluster is created, no need to update such infomation!')
                return
            self.serverCluster_opers.update()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            if isLock:
                zkOper.unLock_sync_server_zk_action(lock)