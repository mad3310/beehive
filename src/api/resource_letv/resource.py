#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import logging

from zk.zkOpers import Common_ZkOpers
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
        zkOper = Common_ZkOpers()
        ip_list = zkOper.get_ips_from_ipPool()
        nodeCount = component_container_cluster_config.nodeCount
        
        if len(ip_list) < nodeCount:
            raise CommonException('ips are not enough!')

    def elect_servers(self, component_container_cluster_config):
        
        '''
            get usable servers and their resource.
        '''
        host_resource_dict = self.retrieve_usable_host_resource(component_container_cluster_config)
        if not host_resource_dict:
            raise CommonException('there is no usable servers!')
        
        '''
           count servers' scores
        '''
        
        resource_weight__score = component_container_cluster_config.resource_weight__score
        
        host_score_dict = self.__count_score(host_resource_dict, resource_weight__score)
        logging.info('host and score:%s' % str(host_score_dict))
        
        '''
            elect servers by their scores
        '''
        score_list = sorted(host_score_dict.values(), reverse=True)
        logging.info('score list :%s' % str(score_list))
        host_list = self.__host_list(score_list, host_score_dict)
        logging.info('select host list :%s' % str(host_list))
        
        '''
            servers available after validating
        '''
        
        node_count = component_container_cluster_config.nodeCount
        if len(host_list) < node_count:
            raise CommonException('the number of usable servers are not enough!')
        
        return host_list[:node_count]

    def __host_list(self, score_list, host_score_dict):
        host_list = []
        for score in score_list:
            for host, _score in host_score_dict.items():
                if score == _score and host not in host_list:
                    host_list.append(host)
        return host_list

    def retrieve_usable_host_resource(self, component_container_cluster_config):
        host_resource_dict = {}
        zkOper = Common_ZkOpers()
        servers_white_list = zkOper.retrieve_servers_white_list()
        _exclude_servers = component_container_cluster_config.exclude_servers
        logging.info('exclude server:%s, type:%s' % (str(_exclude_servers), type(_exclude_servers)))
        host_ip_list = list(set(servers_white_list) - set(_exclude_servers))
        logging.info('hosts choosed:%s' % str(host_ip_list))
        for host_ip in host_ip_list:
            host_resource = self.__get_usable_host_resource(host_ip, component_container_cluster_config)
            if host_resource != {}:
                host_resource_dict.setdefault(host_ip, host_resource)
        return host_resource_dict

    def __count_score(self, host_resource_dict, weight_item_score):
        mem_list, disk_list, container_number_list = [], [], []
        
        host_list = sorted(host_resource_dict)
        for host in host_list:
            resource = host_resource_dict.get(host)
            mem_list.append(resource.get('memory'))
            disk_list.append(resource.get('disk'))
            container_number_list.append(resource.get('container_number'))
        
        weight_memory_score = weight_item_score.get('memory')
        weight_disk_score = weight_item_score.get('disk')
        weight_container_number_score = weight_item_score.get('container_number')
        mem_score_dict = self.__get_item_score(mem_list, weight_memory_score)
        disk_score_dict = self.__get_item_score(disk_list, weight_disk_score)
        container_number_score_dict = self.__get_item_score(container_number_list, weight_container_number_score, reverse=True)
        
        host_score_dict = {}
        for index, host in enumerate(host_list):
            mem_score = mem_score_dict.get(mem_list[index])
            disk_score = disk_score_dict.get(disk_list[index])
            container_number_score = container_number_score_dict.get(container_number_list[index])
            total_score = mem_score + disk_score + container_number_score
            host_score_dict.setdefault(host, total_score)
            
        return host_score_dict

    def __get_item_score(self, item_list, total_score, reverse=False):
        max_value = max(item_list)
        
        result = {}
        for item in item_list:
            
            if reverse:
                '''
                    eg. if no container on server No.1 , then container_num load item 
                        No.1 server get top score
                '''
                item_score = total_score
                if item != 0:
                    item_score = total_score * (max_value - item) / max_value
            else:
                item_score = total_score * item / max_value
            result.setdefault(item, int(item_score))
            
        return result

    def __get_usable_host_resource(self, host_ip, component_container_cluster_config):
        resource_result = {}
        zkOper = Common_ZkOpers()
        server_res = zkOper.retrieveDataNodeServerResource(host_ip)
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
        
        '''
            port condition
        '''
        port_number = server_res['port_number']
        port_condition = port_number > 10
        
        logging.info('mem_condition:%s , disk_condition:%s, port_condition:%s' % (mem_condition, disk_condition, port_condition))
        if mem_condition and disk_condition and port_condition:
            resource_result.setdefault('memory', host_mem_can_be_used)
            resource_result.setdefault('disk', host_disk_can_be_used)
            resource_result.setdefault('container_number', server_res['container_number'])
        logging.info('resource result:%s' % str(resource_result))
        return resource_result

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
