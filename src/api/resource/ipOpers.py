#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 17, 2014

@author: root
'''

import os
import time
import Queue
import logging

from zk.zkOpers import ZkOpers
from utils.autoutil import doInThread
from utils.exceptions import CommonException
from docker.dockerOpers import Docker_Opers

class IpOpers(object):
    '''
    classdocs
    '''
    '''
    @todo: why use Queue? List?
    '''
    store_illegal_ips_queue = Queue.Queue()
    store_all_ips_queue = Queue.Queue()

    zkOper = ZkOpers('127.0.0.1', 2181)
    
    docker_opers = Docker_Opers()
    
    def __init__(self):
        '''
        constructor
        '''
    
    '''
    @todo: the method only invoke the zk.method, what means?
    '''
    def get_ips_from_ipPool(self):
        return self.zkOper.get_ips_from_ipPool()
    
    def write_into_ipPool(self, args_dict):
        ip_segment = args_dict.get('ipSegment')
        ip_count = int(args_dict.get('ipCount'))
        choosed_ip = self._get_needed_ips(ip_segment, ip_count)
        for ip in choosed_ip:
            self.zkOper.write_ip_into_ipPool(ip)
    
    def _get_needed_ips(self, ip_segment, ip_count):
        choosed_ip = []
        ip_list = self.zkOper.get_ips_from_ipPool()
        all_ips = self._get_all_ips(ip_segment)
        ips = list( set(all_ips) - set(ip_list) )
        num = 0
        if len(ips) < ip_count:
            raise CommonException('the ips of this segment is less the the number you need, please apply less ips')
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
        '''
        @todo: same as utils.autoutil.ping_ip_able?
        '''
        cmd = 'ping -w 2 %s' % str(ip)
        ret = os.system(cmd)
        if not ret:
            logging.info('ping ip: %s result :%s' % (ip, str(ret)) )
            return False
        
        host_con_ip_list = self.docker_opers.retrieve_containers_ips()
        if ip in host_con_ip_list:
            return False
        return True

        
    def __ips_legal(self):
        """
        """
        while not self.store_all_ips_queue.empty():
            ip = self.store_all_ips_queue.get(block=False)
            is_lagel = self.__ip_legal(ip)
            if not is_lagel:
                self.store_illegal_ips_queue.put(ip)

    def get_illegal_ips(self, thread_num):
        """check ip pools
           
           thread_num: how many thread to do check if ip is legal
           put all ips in ip pools into store_all_ips_queue,
           do check ip is legal in  threads, if illegal, put illegal ip into store_illegal_ips_queue,
           if all threads end, get illegal ips and return them
        """
        
        illegal_ips, thread_obj_list = [], []
        ip_list = self.zkOper.get_ips_from_ipPool()
        logging.info('ips in ip pool:%s' % str(ip_list) )
        
        logging.info('put all ips in ip pools into store_all_ips_queue')
        
        self.store_all_ips_queue._init(0)
        self.store_all_ips_queue.queue.extend(ip_list)
        
        logging.info('queue size :%s' % str(self.store_all_ips_queue.qsize()) )
        for i in range(thread_num):
            thread_obj = doInThread(self.__ips_legal)
            thread_obj_list.append(thread_obj)
        
        while thread_obj_list:
            succ = []
            for thread_obj in thread_obj_list:
                if not thread_obj.isAlive():
                    succ.append(thread_obj)
            for item in succ:
                thread_obj_list.remove(item)
            time.sleep(0.5)
        
        logging.info('get illegal_ip')
        while not self.store_illegal_ips_queue.empty():
            illegal_ip = self.store_illegal_ips_queue.get(block=False)
            illegal_ips.append(illegal_ip)
        logging.info('illegal_ips :%s' % str(illegal_ips) )
        return illegal_ips
    
    def get_ip_num(self):
        """
            monitor item: get ip num from ip Pool
        """

        ip_list = self.get_ips_from_ipPool()
        return len(ip_list)
    
    def retrieve_ip_resource(self, ip_count):
        ip_list = None
        isLock,lock = self.zkOper.lock_assign_ip()
        try:
            if isLock:
                ip_list = self.zkOper.retrieve_ip(ip_count)
        finally:
            if isLock:
                self.zkOper.unLock_assign_ip(lock)
        return ip_list

