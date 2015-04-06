#!/usr/bin/env python2.6.6
#coding:utf-8

import logging
import kazoo
import time
import sys

from monitor.monitorOpers import ResInfoAsyncHandler, ContainerInfoAsyncHandler
from common.abstractAsyncThread import Abstract_Async_Thread
from zk.zkOpers import ZkOpers

class Monitor_Backend_Handle_Worker(Abstract_Async_Thread):
    
    res_handler = ResInfoAsyncHandler()
    con_handler = ContainerInfoAsyncHandler()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Monitor_Backend_Handle_Worker,self).__init__()

    def run(self):
        isLock, lock = False, None
        
        zkOper = ZkOpers()
        try:
            isLock, lock = zkOper.lock_async_monitor_action()
        except kazoo.exceptions.LockTimeout:
            logging.info("a thread is running the monitor async, give up this oper on this machine!")
            return
        
        if not isLock:
            return
        
        try:
            begin_time = time.time()
            self.__action_monitor_async()
            while True:
                end_time = time.time()
                if int(end_time - begin_time) > (self.timeout - 2):
                    logging.info('release the log, get lock time: %s, release time: %s,\n total time : %s' % (str(begin_time), str(end_time), int(end_time-begin_time) ) )
                    break
            time.sleep(1)
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            if isLock:
                zkOper.unLock_aysnc_monitor_action(lock)
                
            zkOper.close()
            
                
    def __action_monitor_async(self):
        self.res_handler.retrieve_info()
        self.con_handler.retrieve_info()
