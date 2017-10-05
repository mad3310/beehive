#!/usr/bin/env python 2.6.6
#coding:utf-8

import sys
import logging
import functools

from utils import get_zk_address
from exceptions import CommonException
from futures import ThreadPoolExecutor
from tornado.gen import Task
from tornado.ioloop import IOLoop
from tornado import stack_context


def singleton(cls):
    
    instances = {}
    
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


def zk_singleton(cls):
    
    instances = {}
    
    def _zk_singleton(*args, **kw):

        zk_addr, zk_port = get_zk_address()
        if not (zk_addr and zk_port):
            raise CommonException('zookeeper address and port are not written!')

        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        
        if instances[cls].zk is None:
            logging.info('zk client disconnect, init another one')
            instances[cls] = cls(*args, **kw)
        
        return instances[cls]
    return _zk_singleton


default_executor =  ThreadPoolExecutor(10)


def run_on_executor(executor=default_executor):

    def run_on_executor_decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            task = Task(executor.submit, func, *args, **kwargs)
            return task
        return wrapper
    return run_on_executor_decorator


def run_callback(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        callback = kwargs.pop('callback', None)
        assert callback
        try:
            res = func(self, *args, **kwargs)
            callback = stack_context.wrap(callback)
            IOLoop.instance().add_callback(lambda: callback(res))
        except:
            self.write_error(500, exc_info=sys.exc_info())
    return wrapper