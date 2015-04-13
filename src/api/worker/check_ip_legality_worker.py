#!/usr/bin/env python2.6.6
#coding:utf-8

import logging
import kazoo
import sys

from common.abstractAsyncThread import Abstract_Async_Thread
from zk.zkOpers import ZkOpers
from monitor.statusOpers import CheckResIpLegality


class Check_Ip_Legality_Worker(Abstract_Async_Thread):
    
    check_ip_legality = CheckResIpLegality()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Check_Ip_Legality_Worker,self).__init__()

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
            self.check_ip_legality.check()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            if isLock:
                zkOper.unLock_aysnc_monitor_action(lock)
                
            zkOper.close()