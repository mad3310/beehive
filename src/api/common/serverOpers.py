#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 10, 2014

@author: root
'''
import os, time, re
import logging, traceback
import docker

from dockerOpers import Docker_Opers
from abstractContainerOpers import Abstract_Container_Opers
from common.utils.autoutil import *
from helper import *
from zkOpers import ZkOpers
from invokeCommand import InvokeCommand
from tornado.options import options

class UpdateServer(object):
    
    zkOper = ZkOpers('127.0.0.1',2181)
    docker_opers = Docker_Opers()
    
    def __init__(self, host_ip):
        self.host_ip = host_ip
    
    def update(self):
        host_containers = self._get_containers_from_host()
        zk_containers = self._get_containers_from_zookeeper()
        add, delete = self._compare(host_containers, zk_containers)
        for item in add:
            self.update_add_note(item)
        for item in delete:
            self.update_del_note(item)
    
    def update_add_note(self, container_name):
        create_info = self._get_container_info_as_zk(container_name)
        logging.info('create_info as zk: \n%s' % str( create_info ) )
        self._write_container_into_zk(create_info)
        stat_flag = get_container_stat(container_name)
        if stat_flag == 0:
            status = {'status': 'started', 'message': ''}
        else:
            status = {'status': 'stopped', 'message': ''}
        self.zkOper.write_container_status(container_name, status)

    def update_del_note(self, container_name):
        status = {'status': 'destroyed', 'message': ''}
        self.zkOper.write_container_status(container_name, status)
        
    def _get_containers_from_host(self):
        container_name_list = []
        container_info_list = self.docker_opers.containers(all=True)
        for container_info in container_info_list:
            container_name = container_info.get('Names')[0]
            container_name = container_name.replace('/', '')
            container_name_list.append(container_name)
        return container_name_list

    def _get_containers_from_zookeeper(self):
        """
        get containers from zookeeper by host_ip
        """
        
        container_name_list = []
        clusters = self.zkOper.retrieve_cluster_list()
        for cluster in clusters:
            container_ip_list = self.zkOper.retrieve_container_list(cluster)
            for container_ip in container_ip_list:
                container_info = self.zkOper.retrieve_container_node_value(cluster, container_ip)
                hostIp = container_info.get('hostIp')
                if self.host_ip == hostIp:
                    container_name = container_info.get('containerName')
                    container_name_list.append(container_name)
        return container_name_list

    def _compare(self, host_container_list, zk_container_list):
        add = list( set(host_container_list) - set(zk_container_list) )
        delete = list( set(zk_container_list) - set(host_container_list) )
        return add, delete

    def _write_container_into_zk(self, create_info):
        self.zkOper.write_container_node_info(create_info)

    def _get_container_info_as_zk(self, container_name):
        create_info = {}
        inspect = self.docker_opers.inspect_container(container_name)
        if not isinstance(inspect, dict):
            logging.error('get inspect failed')
            return create_info
        create_info.setdefault('hostIp', self.host_ip)
        con_name = inspect.get('Config').get('Hostname')
        create_info.setdefault('containerName', con_name)
        volumes = inspect.get('Config').get('Volumes')
        create_info.setdefault('mountDir', str(volumes) )
        image = inspect.get('Config').get('Image')
        if 'gbalancer' in image:
            create_info.setdefault('type', 'mclustervip')
        else:
            create_info.setdefault('type', 'mclusternode')
        
        cluster = self.zkOper.get_containerClusterName_from_containerName(container_name)
        create_info.setdefault('containerClusterName', cluster)
        Env = inspect.get('Config').get('Env')
        for item in Env:
            if 'ZKID' in item:
                value = self._get_value(item)
                create_info.setdefault('zookeeperId', value)
            elif item.startswith('IP'):
                value = self._get_value(item)
                create_info.setdefault('ipAddr', value)
            elif item.startswith('GATEWAY'):
                value = self._get_value(item)
                create_info.setdefault('gateAddr', value)
            elif item.startswith('NETMASK'):
                value = self._get_value(item)
                create_info.setdefault('netMask', value)
        return create_info

    def _get_value(self, item):
        try:
            value = re.findall('.*=(.*)', item)[0]
            return value
        except:
            logging.error( str(traceback.format_exc()) )


class Server_Opers(Abstract_Container_Opers):
    '''
    classdocs
    '''
    
    def retrieveServerResource(self):
        resource = {'memoryCount':3,'diskCount':500}
        return resource
    
    def update(self):
        host_ip = getHostIp()
        logging.info('host_ip: %s' % host_ip)
        server = UpdateServer(host_ip)
        server.update()
