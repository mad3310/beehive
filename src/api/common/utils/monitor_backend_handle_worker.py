#!/usr/bin/env python2.6.6
#coding:utf-8

import logging
import kazoo
import threading
import time

from common.zkOpers import ZkOpers
from common.monitorOpers import ResInfoAsyncHandler


class Monitor_Backend_Handle_Worker(threading.Thread):
    
    zkOper = ZkOpers('127.0.0.1', 2181)
    ip_handler = ResInfoAsyncHandler()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Monitor_Backend_Handle_Worker,self).__init__()

    def run(self):
        
        isLock, lock = False, None
        try:
            isLock, lock = self.zkOper.lock_async_monitor_action()
        except kazoo.exceptions.LockTimeout:
            logging.info("a thread is running the monitor async, give up this oper on this machine!")
        
        if isLock:
            try:
                begin_time = time.time()
                self.__action_monitor_async()
                while True:
                    end_time = time.time()
                    if int(end_time - begin_time) > (self.timeout - 2):
                        logging.info('release the log, get lock time: %s, release time: %s,\n total time : %s' % (str(begin_time), str(end_time), int(end_time-begin_time) ) )
                        break
                time.sleep(1)
            except Exception, e:
                logging.error(e)
            finally:
                self.zkOper.unLock_aysnc_monitor_action(lock)
                
    def __action_monitor_async(self):
        db_status_dict = self.ip_handler.retrieve_info()
