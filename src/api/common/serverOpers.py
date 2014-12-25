#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 10, 2014

@author: root
'''
import os
import re
import sys
import time
import logging
import docker
import traceback
import commands

from dockerOpers import Docker_Opers
from common.utils.autoutil import *
from helper import *
from zkOpers import ZkOpers
from invokeCommand import InvokeCommand
from tornado.options import options
from container_module import Container
from abstractAsyncThread import Abstract_Async_Thread


class Server_Opers(Abstract_Async_Thread):
    '''
    classdocs
    '''
    
    def retrieveServerResource(self):
        resource = {'memoryCount':3,'diskCount':500}
        return resource
    
    def update(self):
        try:
            logging.info('update server!')
            host_ip = getHostIp()
            logging.info('host_ip: %s' % host_ip)
            server = UpdateServer(host_ip)
            server.update()
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())

    def get_all_containers_mem_load(self):
        try:
            mem_load_dict = {}
            containers = get_all_containers()
            for container in containers:
                conl = ContainerLoad(container)
                mem_load = conl.get_mem_load()
                mem_load_dict.setdefault(container, mem_load)
            return mem_load_dict
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())

    def get_all_containers_under_oom(self):
        containers = get_all_containers()
        alarm_item = []
        for container in containers:
            con = Container(container)
            container_id = con.id()
            conl = ContainerLoad(container)
            under_oom = conl.get_under_oom_value()
            if under_oom:
                alarm_item.append(container)
        return alarm_item

    def _get_containers(self, container_name_list):
        host_cons = get_all_containers()
        return list ( set(host_cons) & set(container_name_list) )

    def open_containers_under_oom(self, container_name_list):
        try:
            result = {}
            containers = self._get_containers(container_name_list)
            for container in containers:
                conl = ContainerLoad(container)
                ret = conl.open_container_under_oom()
                if not ret:
                    logging.error('container %s under oom value open failed' % container)
                result.setdefault(container, ret)
            return result
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())    

    def shut_containers_under_oom(self, container_name_list):
        try:
            result = {}
            containers = self._get_containers(container_name_list)
            for container in containers:
                conl = ContainerLoad(container)
                ret = conl.shut_container_under_oom()
                if not ret:
                    logging.error('container %s under oom value shut down failed' % container)
                result.setdefault(container, ret)
            return result
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info()) 

    def add_containers_memory(self, container_name_list):
        try:
            host_cons = get_all_containers()
            containers = list ( set(host_cons) & set(container_name_list) )
            add_ret = {}
            for container in containers:
                con = container(container)
                inspect_limit_mem = con.memory()
                conl = ContainerLoad(container)
                con_limit_mem = conl.get_con_limit_mem()
                if con_limit_mem == inspect_limit_mem *2:
                    continue
                ret = self.double_limit_mem()
                add_ret.setdefault(container, ret)
            return add_ret
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())

    def get_containers_disk_load(self, container_name_list):
        try:
            result = {}
            containers = self._get_containers(container_name_list)
            for container in containers:
                load = {}
                conl = ContainerLoad(container)
                root_mnt_size, mysql_mnt_size = conl.get_sum_disk_load()
                load.setdefault('root_mount', root_mnt_size)
                load.setdefault('mysql_mount', mysql_mnt_size)
                result.setdefault(container, load)
            return result
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())

    def double_limit_mem(self, ):
        pass


class ContainerLoad(object):

    def __init__(self, container_name):
        self.container_name = container_name
        self.container_id = ''
        if not self.container_id:
            self.container_id = self.get_container_id()
        self.used_mem_path = '/cgroup/memory/lxc/%s/memory.usage_in_bytes' % self.container_id
        self.limit_mem_path = '/cgroup/memory/lxc/%s/memory.limit_in_bytes' % self.container_id
        self.under_oom_path = '/cgroup/memory/lxc/%s/memory.oom_control' % self.container_id
        self.mysql_mnt_path = '/srv/docker/vfs/dir/%s' % self.container_id
        self.root_mnt_path = '/srv/docker/devicemapper/mnt/%s' % self.container_id

    def get_container_id(self):
        con = Container(self.container_name)
        return con.id()

    def get_file_value(self, file_path):
        value = 0
        file_cmd = 'cat %s' % file_path
        if os.path.exists(file_path):
            value = commands.getoutput(file_cmd)
        return value

    def get_dir_size(self, dir_path):
        size = 0
        dir_cmd = 'du -sm %s' % dir_path
        if os.path.exists(dir_path):
            value = commands.getoutput(dir_cmd)
            if value:
                size = re.findall('(.*)\\t.*', ret)[0]
        return size

    def get_con_used_mem(self):
        return float(self.get_file_value(self.used_mem_path) )

    def get_con_limit_mem(self):
        return float(self.get_file_value(self.limit_mem_path))

    def get_under_oom_value(self): 
        value = self.get_file_value(self.under_oom_path)
        under_oom_value = re.findall('.*under_oom (\d)$', value)[0]
        return int(under_oom_value)

    def get_oom_kill_disable_value(self): 
        value = self.get_file_value(self.under_oom_path)
        under_oom_value = re.findall('oom_kill_disable (\d)\\nunder_oom.*', value)[0]
        return int(under_oom_value)
    
    def _change_container_under_oom(self, switch_value):
        if not os.path.exists(self.under_oom_path):
            logging.error(' container: %s under oom path not exist' % self.container_name)
            return
        cmd = 'echo %s > %s' % (switch_value, self.under_oom_path)
        commands.getoutput(cmd)

    def open_container_under_oom(self):
        self._change_container_under_oom(0)
        return self.get_oom_kill_disable_value() == 0

    def shut_container_under_oom(self):
        self._change_container_under_oom(1)
        return self.get_oom_kill_disable_value() == 1

    def get_mem_load(self):
        mem_load_rate, mem_load_dict = 0, {}
        used_mem = self.get_con_used_mem()
        limit_mem = self.get_con_limit_mem()
        
        logging.info('used_mem:%s, limit_mem: %s, mem_load_rate:%s ' % (used_mem, limit_mem, mem_load_rate) )
        if used_mem and limit_mem:
            mem_load_rate =  used_mem / limit_mem
            mem_load_dict.setdefault('used_mem', used_mem)
            mem_load_dict.setdefault('limit_mem', limit_mem)
            mem_load_dict.setdefault('mem_load_rate', mem_load_rate)
        return mem_load_dict

    def get_root_mnt_size(self):
        return self.get_dir_size(self.root_mnt_path)

    def get_mysql_mnt_size(self):
        return self.get_dir_size(self.mysql_mnt_path)

    def get_sum_disk_load(self):
        root_mnt_size = self.get_root_mnt_size()
        mysql_mnt_size = self.get_mysql_mnt_size()
        return root_mnt_size, mysql_mnt_size


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
        server_info = self._get_container_info_as_zk(container_name)
        zk_con_info = self.zkOper.retrieve_container_node_value_from_containerName(container_name)
        if server_info != zk_con_info:
            self.zkOper.write_container_node_value_by_containerName(container_name, server_info)
        
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
                host_ip = container_info.get('host_ip')
                if self.host_ip == host_ip:
                    inspect = container_info.get('inspect')
                    con = Container(inspect=inspect)
                    container_name = con.name()
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
        
        create_info.setdefault('host_ip', self.host_ip)
        image = con.image()
        if 'gbalancer' in image:
            create_info.setdefault('type', 'mclustervip')
        else:
            create_info.setdefault('type', 'mclusternode')
        create_info.setdefault('inspect', con.inspect)
        create_info.setdefault('container_name', container_name)
        return create_info


