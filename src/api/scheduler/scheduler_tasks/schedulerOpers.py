#!/usr/bin/env python2.6.6
#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: root
'''

from tornado.ioloop import PeriodicCallback
from scheduler.worker.threading_exception_handle_worker import Thread_Exception_Handler_Worker
from scheduler.worker.sync_server_zk_worker import Sync_Server_Zk_Worker


class SchedulerOpers(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''PeriodicCallback class init  callback has no params
           so add monitor_timeout  
        
        '''
        
        self.thread_exception_hanlder(5)

        """ sync """
        self.sync_server_zk_handler(240)

    def thread_exception_hanlder(self, action_timeout = 5):

        def __create_worker_exception_handler():
            exception_hanlder_worker = Thread_Exception_Handler_Worker()
            exception_hanlder_worker.start()
        
        if action_timeout > 0:
            _exception_async_t = PeriodicCallback(__create_worker_exception_handler, action_timeout * 1000)
            _exception_async_t.start()

    def sync_server_zk_handler(self, action_timeout):
        
        def __sync_server_zk_woker():
            sync_server_zk_woker = Sync_Server_Zk_Worker()
            sync_server_zk_woker.start()
            
        _worker = PeriodicCallback(__sync_server_zk_woker, action_timeout * 1000)
        _worker.start()
