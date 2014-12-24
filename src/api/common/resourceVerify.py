#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''

import logging

from abstractContainerOpers import Abstract_Container_Opers
from zkOpers import ZkOpers
from tornado.options import options
from utils.autoutil import *

class ResourceVerify():
    
    zkOper = ZkOpers('127.0.0.1', 2181)
    
    def __init__(self, verify_dict):
        self.verify_dict = verify_dict
    
    def check_resource(self):
        result_dict = {}
        error_msg = ''
        nodeCount = self.verify_dict.get('nodeCount')
        ip_list = self.zkOper.get_ips_from_ipPool()
        if len(ip_list) < nodeCount:
            error_msg = 'ips are not enough!'
        ecect_server = ElectServer()
        host_ip_list = ecect_server.elect_server_list(self.verify_dict)
        logging.info('host_ip_list:%s' % str(host_ip_list))
        
        num = 0
        for weighted_value, available_host_num in host_ip_list:
            num += available_host_num
        
        if num < nodeCount:
            error_msg += 'server resource are not enough!'
        
        select_ip_list = self.get_host_ip_list(host_ip_list, nodeCount)
        
        if len(set(select_ip_list)) <= 2:
            error_msg = 'server nums are not enough, two data node can not be on a server!'
        
        logging.info('select_ip_list:%s' % str(select_ip_list))
        result_dict.setdefault('error_msg', error_msg)
        result_dict.setdefault('select_ip_list', select_ip_list)
        return result_dict

    def get_host_ip_list(self, host_ip_list, container_num):

        hostip_num_dict, ip_list = {}, []
         
        for i in range(container_num):
            for index,(host_ip, available_host_num) in enumerate(host_ip_list):
                if available_host_num > 0:
                    ip_list.append(host_ip)
                    host_ip_list[index] = (host_ip, available_host_num - 1)
                if len(ip_list) == container_num:
                    return ip_list
        return ip_list

    
#    def get_host_ip_list(self, host_ip_list, container_num):
#         hostip_num_dict, ip_list = {}, []
#     
#         for host_ip, available_host_num in host_ip_list:
#             hostip_num_dict.setdefault(host_ip, available_host_num)
#         
#         for i in range(container_num):
#             for host_ip, available_host_num in host_ip_list:
#                 if hostip_num_dict.get(host_ip) > 0:
#                     ip_list.append(host_ip)
#                     hostip_num_dict[host_ip] = hostip_num_dict.get(host_ip) - 1
#                 if len(ip_list) == container_num:
#                     return ip_list
#         return ip_list


class ElectServer(Abstract_Container_Opers):
    
    
    def elect_server_list(self, verify_item):
        score_dict, score_list, ips_result  = {}, [], []
        host_ip_list = self.zkOper.retrieve_servers_white_list()
        available_dict = {}
        for host_ip in host_ip_list:
            host_score, available_host_num = self.get_score(host_ip, verify_item)
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
    
    def get_score(self, host_ip, verify_item={}):
        """
        return score and the num of avaliable hosts
        """
        
        mem_free_limit = 0
        mem_limit = verify_item.get('mem_limit')
        server_url = 'http://%s:%s/server/resource' % (host_ip, options.port)
        server_res = http_get(server_url)
        logging.info('server_res: %s' % str(server_res) )
        mem_free_limit = verify_item.get('mem_free_limit')
        if not mem_free_limit:
            mem_free_limit = 10*1024
        mem_usable = float(server_res["response"]["mem_res"]["free"]) - mem_free_limit
        logging.info('mem_usable:%s' %  mem_usable)
        
        if mem_usable and mem_usable < mem_limit:
            weighted_value = 0
            num = 0
        else:
            weighted_value = mem_usable
            num = int(mem_usable/mem_limit)
        return weighted_value, num

