#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import logging

from zk.zkOpers import ZkOpers
from tornado.options import options
from utils import http_get
from utils.exceptions import CommonException


class Resource(object):
    
    def __init__(self):
        '''
        constructor
        '''
        
    def validateResource(self, component_container_cluster_config, server_list):
        zkOper = ZkOpers()
        try:
            ip_list = zkOper.get_ips_from_ipPool()
        finally:
            zkOper.close()
        
        nodeCount = component_container_cluster_config.nodeCount
        """
            ip or port to diff
        """
        if len(ip_list) < nodeCount:
            raise CommonException('ips are not enough!')
        
        if len(server_list) < nodeCount:
            raise CommonException('usable servers are not enough!')
        
    
    def elect_servers(self, component_container_cluster_config):
        host_resource_dict, elect_server_list  = {}, []
        
        zkOper = ZkOpers()
        try:
            host_ip_list = zkOper.retrieve_servers_white_list()
        finally:
            zkOper.close()
        
        for host_ip in host_ip_list:
            host_resource = self.__get_usable_resource(host_ip, component_container_cluster_config)
            if host_resource != {}:
                host_resource_dict.setdefault(host_ip, host_resource)
        
        '''
           var "weight_item_score" will be passed to elect_servers later
        '''
        weight_item_score = {'memory': 50, 'disk': 50}
        host_score_dict = self.__count_score(host_resource_dict, weight_item_score)
        logging.info('host and score:%s' % str(host_score_dict))
        score_list = sorted(host_score_dict)
        for score in score_list:
            _host_ip = host_score_dict.get(score)
            elect_server_list.append(_host_ip)
            
        return elect_server_list

    def __count_score(self, host_resource_dict, weight_item_score):
        mem_list, disk_list = [], []
        
        host_list = sorted(host_resource_dict)
        for host in host_list:
            resource = host_resource_dict.get(host)
            mem_list.append(resource.get('memory'))
            disk_list.append(resource.get('disk'))
        
        weight_memory_score = weight_item_score.get('memory')
        disk_memory_score = weight_item_score.get('disk')
        mem_score_dict = self.__get_item_score(mem_list, weight_memory_score)
        disk_score_dict = self.__get_item_score(disk_list, disk_memory_score)
        
        score_host_dict = {}
        for index, host in enumerate(host_list):
            mem_score = mem_score_dict.get(mem_list[index])
            disk_score = disk_score_dict.get(disk_list[index])
            total_score = mem_score + disk_score
            score_host_dict.setdefault(total_score, host)
            
        return score_host_dict
    
    def __get_item_score(self, item_list, total_score):
        max_value = max(item_list)
        
        result = {}
        for item in item_list:
            item_score = total_score * item / max_value
            result.setdefault(item, int(item_score))
        return result

    def __get_usable_resource(self, host_ip, component_container_cluster_config):
        server_url = 'http://%s:%s/server/resource' % (host_ip, options.port)
        server_res = http_get(server_url)["response"]
        
        '''
            get host usable memory and the condition to create containers
        '''
        host_mem_limit = component_container_cluster_config.mem_free_limit
        host_mem_can_be_used = float(server_res["mem_res"]["free"]) - host_mem_limit/(1024*1024)
        logging.info('memory: %s, host :%s' % (host_mem_can_be_used, host_ip) )

        _mem_limit = component_container_cluster_config.mem_limit
        container_mem_limit = _mem_limit/(1024*1024)
        mem_condition = host_mem_can_be_used > container_mem_limit
        
        
        '''
            get host usable disk and the condition to create containers
        '''
        used_server_disk = server_res['server_disk']['used']
        total_server_disk = server_res['server_disk']['total']
        
        host_disk_usage_limit = component_container_cluster_config.disk_usage
        host_disk_can_be_used_limit = host_disk_usage_limit * total_server_disk
        host_disk_can_be_used = host_disk_can_be_used_limit - used_server_disk
        logging.info('disk: %s, host :%s' % (host_disk_can_be_used, host_ip) )
        disk_condition = host_disk_can_be_used > 0
        
        resource_result = {}
        if mem_condition and disk_condition:
            resource_result.setdefault('memory', host_mem_can_be_used)
            resource_result.setdefault('disk', host_disk_can_be_used)
            
        return resource_result
