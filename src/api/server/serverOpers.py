#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 10, 2014

@author: root
'''
import logging
import sys

from docker_letv.dockerOpers import Docker_Opers
from zk.zkOpers import ZkOpers
from container.container_module import Container
from container.containerOpers import Container_Opers
from common.abstractAsyncThread import Abstract_Async_Thread
from utils import getHostIp
from status.status_enum import Status
from state.stateOpers import StateOpers
from resource_letv.serverResourceOpers import Server_Res_Opers


class Server_Opers(object):
    '''
    classdocs
    '''
    container_opers = Container_Opers()
    
    '''
    @todo: please notice that:Server opers don't reference docker opers.
    whether associated method should be move them into container opers?
    '''
    docker_opers = Docker_Opers()
    
    server_res_opers = Server_Res_Opers()
    
    def update(self):
        host_ip = getHostIp()
        server_update_action = ServerUpdateAction(host_ip)
        server_update_action.start()

    def get_all_containers_mem_load(self):
        load_dict = {}
        containers = self.container_opers.get_all_containers(False)
        for container in containers:
            load = {}
            conl = StateOpers(container)
            mem_load = conl.get_mem_load()
            memsw_load = conl.get_memsw_load()
            load.update(mem_load)
            load.update(memsw_load)
            load_dict.setdefault(container, load)
        return load_dict

    def get_all_containers_under_oom(self):
        containers = self.container_opers.get_all_containers(False)
        alarm_item = []
        for container in containers:
            conl = StateOpers(container)
            under_oom = conl.get_under_oom_value()
            if under_oom:
                alarm_item.append(container)
        return alarm_item

    def _get_containers(self, container_name_list):
        host_cons = self.container_opers.get_all_containers(False)
        return list ( set(host_cons) & set(container_name_list) )

    def open_containers_under_oom(self, container_name_list):
        result = {}
        containers = self._get_containers(container_name_list)
        for container in containers:
            conl = StateOpers(container)
            ret = conl.open_container_under_oom()
            if not ret:
                logging.error('container %s under oom value open failed' % container)
            result.setdefault(container, ret)
        return result

    def shut_containers_under_oom(self, container_name_list):
        result = {}
        containers = self._get_containers(container_name_list)
        for container in containers:
            conl = StateOpers(container)
            ret = conl.shut_container_under_oom()
            if not ret:
                logging.error('container %s under oom value shut down failed' % container)
            result.setdefault(container, ret)
        return result

    def add_containers_memory(self, container_name_list):
        add_ret = {}
        containers = self._get_containers(container_name_list)
        for container in containers:
            _inspect = self.docker_opers.inspect_container(container)
            con = Container(_inspect)
            inspect_limit_mem = con.memory()
            conl = StateOpers(container)
            con_limit_mem = conl.get_con_limit_mem()
            
            if con_limit_mem == inspect_limit_mem *2:
                add_ret.setdefault(container, 'done before, do nothing!')
                continue
            
            ret = conl.double_mem()
            add_ret.setdefault(container, ret)
            
        return add_ret

    def get_containers_disk_load(self, container_name_list):
        result = {}
        containers = self._get_containers(container_name_list)
        for container in containers:
            load = {}
            conl = StateOpers(container)
            root_mnt_size, mysql_mnt_size = conl.get_sum_disk_load()
            load.setdefault('root_mount', root_mnt_size)
            load.setdefault('mysql_mount', mysql_mnt_size)
            result.setdefault(container, load)
        return result
    
    def write_usable_resource_to_zk(self, resource_limit_args):
        server_res = self.server_res_opers.retrieve_host_stat()
         
        zkOper = ZkOpers()
        try:
            host_ip = getHostIp()
            zkOper.writeDataNodeResource(host_ip, server_res)
        finally:
            zkOper.close()


class ServerUpdateAction(Abstract_Async_Thread):

    docker_opers = Docker_Opers()
    container_opers = Container_Opers()

    def __init__(self, host_ip):
        super(ServerUpdateAction, self).__init__()
        self.host_ip = host_ip

    def run(self):
        try:
            logging.info('do update on server : %s' % self.host_ip)
            self.__update()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __update(self):
        host_containers = self._get_containers_from_host()
        zk_containers = self._get_containers_from_zookeeper()
        add, delete, both = self._compare(host_containers, zk_containers)
        
        for item in add:
            self.update_add_node(item)
        for item in delete:
            self.update_del_node(item)
        for item in both:
            self.update_both_node(item)

    def update_both_node(self, container_name):
        status = {}
        server_info = self._get_container_info_as_zk(container_name)
        zk_con_info = self.container_opers.retrieve_container_node_value_from_containerName(container_name)
        if server_info != zk_con_info:
            logging.info('update both node zookeeper info, container name :%s' % container_name)
            self.container_opers.write_container_node_value_by_containerName(container_name, server_info)
        
        server_con_stat = self.container_opers.get_container_stat(container_name)
        zk_con_stat = self.container_opers.retrieve_container_status_from_containerName(container_name)
        if server_con_stat != zk_con_stat:
            status.setdefault('status',  server_con_stat)
            status.setdefault('message',  '')
            self.container_opers.write_container_status_by_containerName(container_name, status)

    def update_add_node(self, container_name):
        create_info = self._get_container_info_as_zk(container_name)
        logging.info('create_info as zk: \n%s' % str( create_info ) )
        self._write_container_into_zk(container_name, create_info)

    def update_del_node(self, container_name):
        status = {'status': Status.destroyed, 'message': ''}
        self.container_opers.write_container_status_by_containerName(container_name, status)

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
        container_name_list, container_info= [], {}
        
        zkOper = ZkOpers()
        try:
            clusters = zkOper.retrieve_cluster_list()
            for cluster in clusters:
                container_ip_list = zkOper.retrieve_container_list(cluster)
                for container_ip in container_ip_list:
                    container_info = zkOper.retrieve_container_node_value(cluster, container_ip)
                    host_ip = container_info.get('hostIp')
                    if self.host_ip == host_ip:
                        if container_info.has_key('containerName'):
                            container_name = container_info.get('containerName')
                        else:
                            inspect = container_info.get('inspect')
                            con = Container(inspect=inspect)
                            container_name = con.name()
                        container_name_list.append(container_name)
        finally:
            zkOper.close()
        
        return container_name_list

    def _compare(self, host_container_list, zk_container_list):
        add = list( set(host_container_list) - set(zk_container_list) )
        delete = list( set(zk_container_list) - set(host_container_list) )
        both = list( set(host_container_list) & set( zk_container_list) )
        return add, delete, both

    def _write_container_into_zk(self, container_name, create_info):
        container_stat = self.container_opers.get_container_stat(container_name)
        self.container_opers.write_container_node_info(container_stat, create_info)
        

    def _get_container_info_as_zk(self, container_name):
        create_info = {}
        _inspect = self.docker_opers.inspect_container(container_name)
        con = Container(_inspect)
        
        create_info.setdefault('hostIp', self.host_ip)
        image = con.image()
        
        '''
        @todo: what means?
        '''
        if 'gbalancer' in image:
            create_info.setdefault('type', 'mclustervip')
        else:
            create_info.setdefault('type', 'mclusternode')
        create_info.setdefault('inspect', con.inspect)
        create_info.setdefault('containerName', container_name)
        return create_info

