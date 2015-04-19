#!/usr/bin/env python2.6.6
#coding:utf-8

import sys
import logging

from common.abstractAsyncThread import Abstract_Async_Thread
from container.containerOpers import Container_Opers


class Record_Containers_Resource_Worker(Abstract_Async_Thread):
    
    container_opers = Container_Opers()
    
    def __init__(self, timeout=55):
        self.timeout = timeout
        super(Record_Containers_Resource_Worker,self).__init__()

    def run(self):
        
        try:
            self.__action_record_containers_resource()
        except Exception:
            self.threading_exception_queue.put(sys.exc_info())
    
    def __action_record_containers_resource(self):
        logging.info('record containers resource')
        resource_items = ['memory', 'cpuacct', 'networkio', 'disk', 'under_oom', 'oom_kill_disable']
        for resource_item in resource_items:
            resource_info = self.container_opers.get_containers_resource(resource_item)
            logging.info('%s info:%s' % (resource_item, str(resource_info) ) )
            self.container_opers.write_containers_resource_to_zk(resource_item, resource_info)