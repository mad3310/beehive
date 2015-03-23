#!/usr/bin/env python2.6.6
#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: root
'''

from tornado.ioloop import PeriodicCallback
from utils.threading_exception_handle_worker import Thread_Exception_Handler_Worker
from utils.monitor_backend_handle_worker import Monitor_Backend_Handle_Worker


class Sceduler_Opers(object):
    '''
    classdocs
    '''
    
    def __init__(self, monitor_timeout=55):
        '''PeriodicCallback class init  callback has no params
           so add monitor_timrout  
        
        '''
        
        self.monitor_timeout = monitor_timeout
        self.thread_exception_hanlder(5)
        self.sced_monitor_handler(55)

    def sced_monitor_handler(self, action_timeout = 30):
        """Create a periodic callback that tries to access async monitor interface
        
           action_timeout: default monitor timeout
        """
        
        if action_timeout > 0:
            _monitor_async_t = PeriodicCallback(self.__create_worker_check_monitor,
                                                action_timeout * 1000)
            _monitor_async_t.start()
    
    '''
    @todo: the different of action_timeout and monitor_timeout
    reason: the callback of the class PeriodicCallback have no params 
    
    '''
    def __create_worker_check_monitor(self):
        monitor_backend_worker = Monitor_Backend_Handle_Worker(self.monitor_timeout)
        monitor_backend_worker.start()

    def thread_exception_hanlder(self, action_timeout = 5):
        if action_timeout > 0:
            _exception_async_t = PeriodicCallback(self.__create_worker_exception_handler,
                                                  action_timeout * 1000)
            _exception_async_t.start()

    def __create_worker_exception_handler(self):
        exception_hanlder_worker = Thread_Exception_Handler_Worker()
        exception_hanlder_worker.start()

