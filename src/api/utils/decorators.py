#!/usr/bin/env python 2.6.6
#coding:utf-8

from utils import get_zk_address
from exceptions import CommonException

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
            instances[cls] = cls(*args, **kw)
        
        return instances[cls]
    return _zk_singleton