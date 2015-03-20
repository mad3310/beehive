#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import logging

from zk.zkOpers import ZkOpers
from tornado.options import options
from utils.autoutil import http_get
from utils.exceptions import CommonException

class ResourceVerify(object):
    
    zkOper = ZkOpers()
    
    
    def __init__(self):
        '''
        constructor
        '''
    
    def check_resource(self, component_container_cluster_config):
        usable_hostip_num_list = []
        nodeCount = component_container_cluster_config.nodeCount
        ip_list = self.zkOper.get_ips_from_ipPool()
        
        """
            ip or port to diff
        """
        if len(ip_list) < nodeCount:
            raise CommonException('ips are not enough!')
        
        elect_server = ElectServer()
        usable_hostip_num_list = elect_server.elect_server_list(component_container_cluster_config)
        logging.info('usable_hostip_num_list:%s' % str(usable_hostip_num_list))
        
        num = 0
        for weighted_value, available_host_num in usable_hostip_num_list:
            num += available_host_num
        
        if num < nodeCount:
            raise CommonException('usable servers are not enough!')
            
        '''
        @todo: add the ckeck logic for the rest value of disk,if the disk usage > 70%, then throw exception
        '''
        return usable_hostip_num_list

    def get_create_containers_hostip_list(self, usable_hostip_num_list, component_container_cluster_config):
        nodeCount = component_container_cluster_config.nodeCount
        select_ip_list = self.__get_host_ip_list(usable_hostip_num_list, nodeCount)
        
        if not self.check_hosts_illegal(select_ip_list, component_container_cluster_config):
            raise CommonException('two mcluster data nodes are on a server, illegal!')
        return select_ip_list

    def check_hosts_illegal(self, select_ip_list, component_container_cluster_config):
        """mcluster data nodes can't be on a server 
        
        """
        is_illegal = True
        component_type = component_container_cluster_config.component_type
        if component_type =='mclusternode':
            nodeCount = component_container_cluster_config.nodeCount
            if len(select_ip_list) != nodeCount:
                is_illegal = False
        elif component_type =='mclustervip':
            pass
        else:
            pass
        return is_illegal

    def __get_host_ip_list(self, host_ip_list, container_num):

        ip_list = []
        
        for i in range(container_num):
            for index,(host_ip, available_host_num) in enumerate(host_ip_list):
                if available_host_num > 0:
                    ip_list.append(host_ip)
                    host_ip_list[index] = (host_ip, available_host_num - 1)
                if len(ip_list) == container_num:
                    return ip_list
        return ip_list

    
class ElectServer(object):
    
    zkOper = ZkOpers()
    
    def elect_server_list(self, component_container_cluster_config):
        score_dict, score_list, ips_result  = {}, [], []
        host_ip_list = self.zkOper.retrieve_servers_white_list()
        available_dict = {}
        for host_ip in host_ip_list:
            host_score, available_host_num = self.__get_score(host_ip, component_container_cluster_config)
            if host_score != 0 :
                score_dict.setdefault(host_ip, host_score)
                available_dict.setdefault(host_ip, available_host_num)
                score_list.append(host_score)
        
        score_list.sort(reverse=True)
        for score in score_list:
            for _host_ip,_host_score in score_dict.items():
                host_array = (_host_ip, available_dict.get(_host_ip))
                if _host_score == score and host_array not in ips_result:
                    ips_result.append((_host_ip, available_dict.get(_host_ip)))
                    break
        return ips_result
    
    def __get_score(self, host_ip, component_container_cluster_config):
        """
            return score and the num of avaliable hosts
            mem_free_limit: memory can be used on a server
            mem_limit: memory limit on container config
        """
        
        '''
        foucs on mem_limit
        what means mem_limit and mem_free_limit?
        '''
        
        weighted_value, num = 0, 0 
        _mem_limit = component_container_cluster_config.mem_limit
        mem_limit = _mem_limit/(1024*1024)
        
        server_url = 'http://%s:%s/server/resource' % (host_ip, options.port)
        _server_res = http_get(server_url)
        server_res = _server_res["response"]
        logging.info('server_res: %s' % str(server_res) )
        mem_free_limit = component_container_cluster_config.mem_free_limit
        
        mem_usable = float(server_res["mem_res"]["free"]) - mem_free_limit/(1024*1024)
        logging.info('mem_usable:%s' %  mem_usable)
        
        rest_server_disk = server_res['server_disk']['free']
        total_server_disk = server_res['server_disk']['total']
        logging.info('rest disk :%s, total disk:%s' % (rest_server_disk, total_server_disk) )
        disk_condition = float(rest_server_disk)/total_server_disk < 0.7
        mem_condition = mem_usable > mem_limit
        
        if mem_condition and disk_condition:
            weighted_value = mem_usable
            num = int(mem_usable/mem_limit)
        
        return weighted_value, num
