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
from container_module import Container

class UpdateServer(object):
    
    zkOper = ZkOpers('127.0.0.1',2181)
    docker_opers = Docker_Opers()
    
    def __init__(self, host_ip):
        self.host_ip = host_ip
    
    def update(self):
        host_containers = self._get_containers_from_host()
        zk_containers = self._get_containers_from_zookeeper()
        add, delete, both = self._compare(host_containers, zk_containers)

        for item in add:
            self.update_add_note(item)
        for item in delete:
            self.update_del_note(item)
        for item in both:
            self.update_both_note(item)

    def update_both_note(self, container_name):
        status = {}
        server_con_stat = get_container_stat(container_name)
        zk_con_stat = self.zkOper.retrieve_container_status_from_containerName(container_name)
        if server_con_stat != zk_con_stat:
            status.setdefault('status',  server_con_stat)
            status.setdefault('message',  '')
        self.zkOper.write_container_status_by_containerName(container_name, status)

    def update_add_note(self, container_name):
        status = {}
        create_info = self._get_container_info_as_zk(container_name)
        logging.info('create_info as zk: \n%s' % str( create_info ) )
        self._write_container_into_zk(container_name, create_info)

    def update_del_note(self, container_name):
        status = {'status': 'destroyed', 'message': ''}
        self.zkOper.write_container_status_by_containerName(container_name, status)

    def _get_containers_from_host(self):
        container_name_list = []
        container_info_list = self.docker_opers.containers(all=True)
        for container_info in container_info_list:
            container_name = container_info.get('Names')[0]
            container_name = container_name.replace('/', '')
            container_name_list.append(container_name)
        return container_name_list

    def _get_containers_from_zookeeper(self):
        """if the status container in zookeeper is destroyed, regard this container as not exist.
        
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
        both = list( set(host_container_list) & set( zk_container_list) )
        return add, delete, both

    def _write_container_into_zk(self, container_name, create_info):
        container_stat = get_container_stat(container_name)
        self.zkOper.write_container_node_info(container_stat, create_info)

    def _get_container_info_as_zk(self, container_name):
        create_info = {}
        con = Container(container_name)
        
        create_info.setdefault('hostIp', self.host_ip)
        image = con.image()
        if 'gbalancer' in image:
            create_info.setdefault('type', 'mclustervip')
        else:
            create_info.setdefault('type', 'mclusternode')
        create_info.setdefault('inspect', con.inspect)
        return create_info


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
