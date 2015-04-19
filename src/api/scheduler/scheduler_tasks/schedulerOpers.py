#!/usr/bin/env python2.6.6
#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: root
'''

from tornado.ioloop import PeriodicCallback
from scheduler.worker.threading_exception_handle_worker import Thread_Exception_Handler_Worker
from scheduler.worker.monitor_check_worker import Monitor_Check_Worker
from scheduler.worker.record_servers_resource_worker import Record_Servers_Resource_Worker
from scheduler.worker.sync_server_zk_worker import Sync_Server_Zk_Worker
from scheduler.worker.check_ip_legality_worker import Check_Ip_Legality_Worker
from scheduler.worker.record_containers_resource_worker import Record_Containers_Resource_Worker


class SchedulerOpers(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''PeriodicCallback class init  callback has no params
           so add monitor_timrout  
        
        '''
        
        self.thread_exception_hanlder(5)
        self.check_ip_legality_handler(600)
        self.sync_server_zk_handler(240)
        

        '''
            for update and monitor server resource
        '''
        self.record_servers_resource_handler(10)
        
        '''
            for monitor containers resource and webportal paint resource picture
        '''
        self.record_containers_resource_handler(25)
        
        self.monitor_check_handler(55)
        
    def record_containers_resource_handler(self, action_timeout):
        
        def __record_containers_resource_woker():
            _woker = Record_Containers_Resource_Worker(action_timeout)
            _woker.start()
            
        _worker = PeriodicCallback(__record_containers_resource_woker, action_timeout * 1000)
        _worker.start()

    def check_ip_legality_handler(self, action_timeout):
        
        def __check_ip_legality_woker():
            sync_server_zk_woker = Check_Ip_Legality_Worker(action_timeout)
            sync_server_zk_woker.start()
            
        _worker = PeriodicCallback(__check_ip_legality_woker, action_timeout * 1000)
        _worker.start()

    def sync_server_zk_handler(self, action_timeout):
        
        def __sync_server_zk_woker():
            sync_server_zk_woker = Sync_Server_Zk_Worker()
            sync_server_zk_woker.start()
            
        _worker = PeriodicCallback(__sync_server_zk_woker, action_timeout * 1000)
        _worker.start()

    def record_servers_resource_handler(self, action_timeout):
        
        def __record_resource_woker():
            record_servers_resource_worker = Record_Servers_Resource_Worker(action_timeout)
            record_servers_resource_worker.start()
            
        _worker = PeriodicCallback(__record_resource_woker, action_timeout * 1000)
        _worker.start()

#     def monitor_record_handler(self, action_timeout = 55):
#         """Create a periodic callback that tries to access async monitor interface
#            action_timeout: default monitor timeout
#         """
#         
#         def __monitor_record_worker():
#             monitor_record_worker = Monitor_Record_Worker(action_timeout)
#             monitor_record_worker.start()
# 
#         if action_timeout > 0:
#             _monitor_async_t = PeriodicCallback(__monitor_record_worker, action_timeout * 1000)
#             _monitor_async_t.start()

    def monitor_check_handler(self, action_timeout = 55):
        
        def __monitor_check_worker():
            monitor_check_worker = Monitor_Check_Worker(action_timeout)
            monitor_check_worker.start()
        
        if action_timeout > 0:
            _monitor_async_t = PeriodicCallback(__monitor_check_worker, action_timeout * 1000)
            _monitor_async_t.start()

    def thread_exception_hanlder(self, action_timeout = 5):

        def __create_worker_exception_handler():
            exception_hanlder_worker = Thread_Exception_Handler_Worker()
            exception_hanlder_worker.start()
        
        if action_timeout > 0:
            _exception_async_t = PeriodicCallback(__create_worker_exception_handler, action_timeout * 1000)
            _exception_async_t.start()

#     def __create_worker_exception_handler(self):
#         exception_hanlder_worker = Thread_Exception_Handler_Worker()
#         exception_hanlder_worker.start()
