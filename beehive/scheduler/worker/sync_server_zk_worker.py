#!/usr/bin/env python2.6.6
#coding:utf-8

import sys
import logging

from zk.zkOpers import Scheduler_ZkOpers
from common.abstractAsyncThread import Abstract_Async_Thread
from server.serverOpers import Server_Opers


class Sync_Server_Zk_Worker(Abstract_Async_Thread):
    
    server_opers = Server_Opers()
    
    def __init__(self):
        super(Sync_Server_Zk_Worker, self).__init__()

    def run(self):
        logging.info('do sync server')
        zkOper = Scheduler_ZkOpers()
        try:
            cluster_list = zkOper.retrieve_cluster_list()
            if not cluster_list:
                logging.info('no cluster is created, no need to update such infomation!')
                return
            self.server_opers.sync()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
