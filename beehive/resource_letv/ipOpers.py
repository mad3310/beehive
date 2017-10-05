#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 17, 2014

@author: root
'''

import time
import logging
import re
import kazoo

from utils import ping_ip_available
from utils.threadUtil import doInThread
from docker_letv.dockerOpers import Docker_Opers
from zk.zkOpers import Common_ZkOpers


class IpOpers(object):
    '''
    classdocs
    '''

    docker_opers = Docker_Opers()
    
    def __init__(self):
        '''
        constructor
        '''
    
    def write_into_ipPool(self, args_dict):
        doInThread(self._write_into_ipPool, args_dict)

    def _write_into_ipPool(self, args_dict):
        ip_segment = args_dict.get('ipSegment')
        ip_count = int(args_dict.get('ipCount'))
        choosed_ip = self._get_needed_ips(ip_segment, ip_count)
        
        zkOper = Common_ZkOpers()
        
        for ip in choosed_ip:
            zkOper.write_ip_into_ipPool(ip)

    def _get_needed_ips(self, ip_segment, ip_count):
        choosed_ip = []
        
        zkOper = Common_ZkOpers()
        ip_list = zkOper.get_ips_from_ipPool()
        
        all_ips = self._get_all_ips(ip_segment)
        ips = list( set(all_ips) - set(ip_list) )
        num = 0
        if len(ips) < ip_count:
            logging.info('ips usable are not enough, just add %s ips' % len(ips))
            ip_count = len(ips)

        for ip in ips:
            if self.__ip_legal(ip):
                choosed_ip.append(ip)
                num += 1
            if num == ip_count:
                break
        return choosed_ip
    
    def _get_all_ips(self, ip_segment):
        all_ips = []
        ip_items = ip_segment.split('.')
        for i in range(2, 254):
            ip_items[-1] = str(i)
            ip = '.'.join(ip_items)
            all_ips.append(ip)
        return all_ips       

    def __ip_legal(self, ip):
        ip_pattern = '((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)'
        if not re.match(ip_pattern, ip):
            logging.info('ip :%s not legal in pool' % ip)
            return False
        
        ret = ping_ip_available(ip)
        if ret:
            logging.info('ping ip: %s result :%s' % (ip, str(ret)) )
            return False
        
        host_con_ip_list = self.docker_opers.retrieve_containers_ips()
        if ip in host_con_ip_list:
            return False
        return True

    def retrieve_ip_resource(self, ip_count, try_times=5):
        n = 0
        while n < try_times:
            n += 1
            ip_list = self.do_retrieve_ip_action(ip_count)
            if ip_list:
                return ip_list
            time.sleep(1)

    def do_retrieve_ip_action(self, ip_count):
        ip_list, isLock = None, None
        
        zkOper = Common_ZkOpers()
        try:
            isLock,lock = zkOper.lock_assign_ip()
            if isLock:
                ip_list = zkOper.retrieve_ip(ip_count)
        except kazoo.exceptions.LockTimeout:
            return
            
        finally:
            if isLock:
                zkOper.unLock_assign_ip(lock)
            
        return ip_list

