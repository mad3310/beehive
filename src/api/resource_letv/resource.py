#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import logging

from zk.zkOpers import ZkOpers
from tornado.options import options
from utils.exceptions import CommonException
from resource_letv.ipOpers import IpOpers
from resource_letv.portOpers import PortOpers


class Resource(object):
    
    ipOpers = IpOpers()
    
    portOpers = PortOpers()
    
    def __init__(self):
        '''
        constructor
        '''

    def validateResource(self, component_container_cluster_config):
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

    def retrieve_best_resource_servers(self, component_container_cluster_config):
        zkOper = ZkOpers()
        try:
            available_item_dict = zkOper.retrieve_available_item()
            available_item = available_item_dict.get('available_item')
            if available_item not in ['s0','s1']:
                raise CommonException("error available_item, not [s0,s1], please confirm zk value!")
            
            best_resource_ips = zkOper.retrieve_servers_order_by_resource(available_item)
            
        finally:
            zkOper.close()
            
        node_count = component_container_cluster_config.nodeCount
            
        if len(best_resource_ips) < node_count:
            raise CommonException('usable servers are not enough!')
        
        return best_resource_ips[:node_count]


    '''
    @##
    '''
    def elect_servers(self, component_container_cluster_config):
        host_resource_dict, elect_server_list  = {}, []
        
        zkOper = ZkOpers()
        try:
            host_ip_list = zkOper.retrieve_servers_white_list()
            for host_ip in host_ip_list:
                host_resource = zkOper.retrieveDataNodeResource(host_ip)
                if host_resource != {}:
                    host_resource_dict.setdefault(host_ip, host_resource)
                    
            '''
               var "weight_item_score" will be passed to elect_servers later
            '''
            weight_item_score = {
                'memory': 20, 
                'disk': 20, 
                'load5': 20, 
                'load10': 10, 
                'load15': 5, 
                'container_number': 15
            }
            
            host_score_dict = self.__count_score(host_resource_dict, weight_item_score)
            logging.info('host and score:%s' % str(host_score_dict))
            score_list = sorted(host_score_dict)
            for score in score_list:
                _host_ip = host_score_dict.get(score)
                elect_server_list.append(_host_ip)
                
            current_available_item = zkOper.retrieve_available_item()
            
            available_item = 's1' if current_available_item == 's0' else 's0'
            zkOper.write_servers_order_by_resource(available_item, elect_server_list)
            
        finally:
            zkOper.close()

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
            '''
            @todo: what means? total_score * item / max_value
            '''
            item_score = total_score * item / max_value
            result.setdefault(item, int(item_score))
            
        return result

    def retrieve_ip_port_resource(self, host_ip_list, component_container_cluster_config):
        containerCount = component_container_cluster_config.nodeCount
        _network_mode = component_container_cluster_config.network_mode 
        
        ip_port_resource_list = []
        if 'ip' == _network_mode:
            ip_port_resource_list = self.ipOpers.retrieve_ip_resource(containerCount)
        elif 'bridge' == _network_mode:
            ports = component_container_cluster_config.ports
            ip_port_resource_list = self.portOpers.retrieve_port_resource(host_ip_list, len(ports))
            
        return ip_port_resource_list
