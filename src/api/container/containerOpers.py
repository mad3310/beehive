#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''


import os
import sys
import logging
import traceback
import pexpect

from common.abstractContainerOpers import Abstract_Container_Opers
from common.abstractAsyncThread import Abstract_Async_Thread
from docker_letv.dockerOpers import Docker_Opers
from container.container_model import Container_Model
from utils.exceptions import CommonException, RetryException, UserVisiableException
from utils.log import _log_docker_run_command
from utils import _mask_to_num, get_current_time, getHostIp
from zk.zkOpers import ZkOpers
from docker import Client
from status.status_enum import Status
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from utils import get_containerClusterName_from_containerName
from state.stateOpers import StateOpers


class Container_Opers(Abstract_Container_Opers):
    
    docker_opers = Docker_Opers()
    component_manager_status_validator = ComponentManagerStatusValidator()
    
    def __init__(self):
        '''
        Constructor
        '''

    def create(self, docker_model):
        container_create_action = Container_create_action(docker_model)
        container_create_action.start()
 
    def stop(self, container_name):
        container_stop_action = Container_stop_action(container_name)
        container_stop_action.start()

    def start(self, container_name):
        container_start_action = Container_start_action(container_name)
        container_start_action.start()

    def destroy(self, container_name):
        container_destroy_action = Container_destroy_action(container_name)
        container_destroy_action.start()

    def check(self, container_name):
        exists = self.check_container_exists(container_name)
        if not exists:
            raise UserVisiableException("container(name:%s) dont's existed!" % (container_name))
        
        container_operation_record = self.retrieve_container_status_from_containerName(container_name)
        status = container_operation_record.get('status')
        message = container_operation_record.get('message')
        
        result = {}
        result.setdefault('status', status)
        result.setdefault('message', message)
        return result

    def get_container_stat(self, container_name):
        """
        """
        exists = self.check_container_exists(container_name)
        if not exists:
            return Status.destroyed
        
        container_info_list = self.docker_opers.containers(all=True)
        
        for container_info in container_info_list:
            name = container_info.get('Names')[0]
            name = name.replace('/', '')
            if name == container_name:
                stat = container_info.get('Status')
                if 'Up' in stat:
                    return Status.started
                elif 'Exited' in stat:
                    return Status.stopped

    def get_all_containers(self, is_all=True):
        """get all containers on some server
        
        all -> True  all containers on such server
        all -> False  started containers on such server
        """
        container_name_list = []
        container_info_list = self.docker_opers.containers(all=is_all)
        for container_info in container_info_list:
            name = container_info.get('Names')[0]
            name = name.replace('/', '')
            container_name_list.append(name)
        return container_name_list

    def check_container_exists(self, container_name):
        container_name_list = self.get_all_containers()
        return_result = container_name in container_name_list
        return return_result

    def manager_status_validate(self, component_type, container_name):
        return self.component_manager_status_validator.validate_manager_status_for_container(component_type, container_name) 

    def get_container_node_from_container_name(self, cluster, container_name):
        con_node = ''
        
        zkOper = ZkOpers()
        try:
            cluster_info = zkOper.retrieve_container_cluster_info(cluster)
            use_ip = cluster_info.get('isUseIp')
            if use_ip:
                container_node_list = zkOper.retrieve_container_list(cluster)
                for container_node in container_node_list:
                    container_info = zkOper.retrieve_container_node_value(cluster, container_node)
                    inspect = container_info.get('inspect')
                    con = Container_Model(inspect=inspect)
                    con_name = con.name()
                    if container_name == con_name:
                        con_node = container_node
                        break
            else:
                con_node = container_name
        finally:
            zkOper.close()
        
        return con_node

    def retrieve_container_node_value_from_containerName(self, container_name):
        cluster = get_containerClusterName_from_containerName(container_name)
        container_node = self.get_container_node_from_container_name(cluster, container_name)
        
        zkOper = ZkOpers()
        try:
            node_value = zkOper.retrieve_container_node_value(cluster, container_node)
        finally:
            zkOper.close()
            
        return node_value

    def retrieve_container_status_from_containerName(self, container_name):
        cluster = get_containerClusterName_from_containerName(container_name)
        container_node = self.get_container_node_from_container_name(cluster, container_name)
        
        zkOper = ZkOpers()
        try:
            status_value = zkOper.retrieve_container_status_value(cluster, container_node)
        finally:
            zkOper.close()
            
        return status_value

    def write_container_node_value_by_containerName(self, container_name, container_props):
        """only write container value and not write status value
        
        """
        cluster = get_containerClusterName_from_containerName(container_name)
        container_node = self.get_container_node_from_container_name(cluster, container_name)
        
        zkOper = ZkOpers()
        try:
            zkOper.write_container_node_value(cluster, container_node, container_props)
        finally:
            zkOper.close()
        
    def write_container_status_by_containerName(self, container_name, record):
        containerClusterName = get_containerClusterName_from_containerName(container_name)
        container_node = self.get_container_node_from_container_name(containerClusterName, container_name)
        
        zkOper = ZkOpers()
        try:
            zkOper.write_container_status(containerClusterName, container_node, record)
        finally:
            zkOper.close()
        

    def get_container_name_from_zk(self, cluster, container_node):
        zkOper = ZkOpers()
        try:
            container_info = zkOper.retrieve_container_node_value(cluster, container_node)
        finally:
            zkOper.close()
        
        inspect = container_info.get('inspect')
        con = Container_Model(inspect=inspect)
        return con.name()

    def get_host_ip_from_zk(self, cluster, container_node):
        zkOper = ZkOpers()
        try:
            container_info = zkOper.retrieve_container_node_value(cluster, container_node)
        finally:
            zkOper.close()
        
        return container_info.get('hostIp')
    
    def write_container_node_info_to_zk(self, container_stat, containerProps):
        
        inspect = containerProps.get('inspect')
        is_use_ip =  containerProps.get('isUseIp')
        con = Container_Model(inspect=inspect)
        container_name = con.name()
        cluster = con.cluster(container_name)
        logging.info('get container cluster :%s' % cluster)
        if is_use_ip:
            container_node = con.ip()
            logging.info('get container ip :%s' % container_node)
            if not (container_node and cluster):
                raise CommonException('get container ip or cluster name failed, not write this info, inspect:%s' % (inspect))
            
            container_node = container_node
        else:
            container_node = container_name
            
        zkOper = ZkOpers()
        try:
            zkOper.write_container_node_info(cluster, container_node, container_stat, containerProps)
        finally:
            zkOper.close()

    def get_all_containers_under_oom(self):
        containers = self.get_all_containers(False)
        alarm_item = []
        for container in containers:
            conl = StateOpers(container)
            under_oom = conl.get_under_oom_value()
            if under_oom:
                alarm_item.append(container)
        return alarm_item

    def _get_containers(self, container_name_list):
        host_cons = self.get_all_containers(False)
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
            con = Container_Model(_inspect)
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

    def get_containers_resource(self, resource_type):
        '''
            resource_type: memory, networkio, cpuacct, disk and so on.
        '''
        
        container_name_list = self.get_all_containers(False)
        if not container_name_list:
            return {}
        
        resource_func_dict = {'memory' : 'get_memory_stat_item',
                              'cpuacct' : 'get_cpuacct_stat_item',
                              'networkio' : 'get_network_io',
                              'disk' : 'get_sum_disk_load', 
                              'under_oom' : 'get_under_oom_value', 
                              'oom_kill_disable' : 'get_oom_kill_disable_value',
                              }
                
        resource_info, resource_item, container_resource = {}, {}, {}
        current_time = get_current_time()
        for container_name in container_name_list:
            state_opers = StateOpers(container_name)
            _method = resource_func_dict.get(resource_type)
            resource_item = getattr(state_opers, _method)()
            container_resource.setdefault(container_name, resource_item)
            
        resource_info.setdefault(str(resource_type), container_resource)
        resource_info.setdefault('time', current_time)
        return resource_info

    def write_containers_resource_to_zk(self, resource_type, resource_info):
        zkOper = ZkOpers()
        try:
            host_ip = getHostIp()
            zkOper.writeDataNodeContainersResource(host_ip, resource_type, resource_info)
        finally:
            zkOper.close()


class Container_create_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    container_opers = Container_Opers()
    
    def __init__(self, docker_model):
        super(Container_create_action, self).__init__()
        self.docker_model = docker_model

    def run(self):
        try:
            logging.info('begin create container')
            self.__issue_create_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_create_action(self):
        
        self.__make_mount_dir()
        
        self.issue_image()
        
        _log_docker_run_command(self.docker_model)
        '''
        orginal:
            image=image_name, 
            hostname=container_name,
            name=container_name, 
            environment=env, 
            ports=_ports,
            mem_limit=_mem_limit, 
            volumes=_volumes
        '''
        self.docker_opers.create(self.docker_model)
        
        '''
        orginal:
            container_name, 
            privileged=True, 
            network_mode='bridge', 
            binds=_binds
        '''
        self.docker_opers.start(self.docker_model)
        
        if self.docker_model.use_ip:
            init_con_ret = self.set_ip_add_route_retry(3)
            if not init_con_ret:
                error_message = 'set_ip_add_route_retry container failed'
                logging.error(error_message)
                raise CommonException(error_message)
        
        result = self.__check_create_status()
        if not result:
            error_message = 'the exception of creating container'
            logging.error(error_message)
            raise CommonException(error_message)
        
        container_node_info = self._get_container_info()
        logging.info('get container info: %s' % str(container_node_info))
        
        self.container_opers.write_container_node_info_to_zk(Status.started, container_node_info)

    def issue_image(self):
        image = self.docker_model.image
        logging.info('create container image :%s' % image)
        exist = self.docker_opers.image_exist(image)
        if not exist:
            if not self.docker_opers.pull(image):
                raise CommonException('pull image %s failed, please check reason' % image)
    
    def __make_mount_dir(self):
        binds = self.docker_model.binds
        if binds:
            for server_dir,_ in binds.items():
                if not os.path.exists(server_dir):
                    os.makedirs(server_dir)
            
            """other component_type have different logic, use elif and else to diff 
               
            """

    def __check_create_status(self):
        container_name = self.docker_model.name
        stat = self.container_opers.get_container_stat(container_name)
        if stat == Status.started:
            return True
        else:
            return False

    def set_ip_add_route_retry(self, retryCount):
        
        container_name = self.docker_model.name
        
        ret = False
        
        while retryCount:
            try:
                self.__set_ip_add_route(container_name)
            except:
                err_msg = str(traceback.format_exc())
                logging.info(err_msg)
                raise RetryException(err_msg)
            ret = True
            break
            retryCount -= 1
        return ret

    def __set_ip_add_route(self, container_name=None):
        timeout = 5
        
        _inspect = self.docker_opers.inspect_container(container_name)
        con = Container_Model(_inspect)
        ip = con.ip()
        mask = con.netmask()
        
        real_route = ''
        for i in range(0,4):
            if i != 3:
                real_route = real_route + str(int(ip.split(r".")[i])&int(mask.split(r".")[i])) + r"."
            else:
                real_route = real_route + str((int(ip.split(r".")[i])&int(mask.split(r".")[i]))+1)
                
        child = pexpect.spawn(r"docker attach %s" % (container_name))
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout)
            r_list = self.__retrieve_route_list(child, timeout)
            if len(r_list) > 0:
                for route in r_list:
                    if route['route_ip'] == real_route:
                        continue
                    else:
                        child.sendline(r"route del -net 0.0.0.0/%s gw %s dev %s" % (route['mask_num'], route['route_ip'], route['dev']))
                        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout)
                        
            r_list = self.__retrieve_route_list(child, timeout)
            logging.info('r_list:%s' % str(r_list) )
            if len(r_list) == 0:
                child.sendline(r"route add default gw %s" % (real_route))
                child.expect(["#", pexpect.EOF, pexpect.TIMEOUT], timeout)
                child.sendline(r"")
            elif len(r_list) > 1 or r_list[0]['route_ip'] != real_route:
                raise RetryException("error")
            else:
                pass
        finally:
            child.close()

    def __retrieve_route_list(self, child, timeout=5):
        get_route_cmd = r"route -n|grep -w 'UG'"
        child.sendline(get_route_cmd)
        child.expect(['0.0.0.0.*bash', pexpect.EOF, pexpect.TIMEOUT], timeout)
        
        if child.after == pexpect.TIMEOUT:
            route_list = []
        else:
            route_list = child.after.replace('bash','').split("\r\n")
            
        logging.info("route_list: %s" % str(route_list))
        r_list = self.__get_route_dicts(route_list)
        if isinstance(r_list, dict):
            if r_list.has_key('false'):
                error_message = str(r_list['false'])
                logging.error(error_message)
            else:
                error_message = 'unknow error: %s' % (str(r_list))
                logging.error(error_message)
            raise RetryException(error_message)
        
        return r_list

    def _get_container_info(self):
        container_name = self.docker_model.name
        _inspect = self.docker_opers.inspect_container(container_name)
        con = Container_Model(_inspect)
        container_node_info= {}
        container_node_info.setdefault('containerName', container_name)
        container_node_info.setdefault('inspect', con.inspect)
        container_node_info.setdefault('hostIp', self.docker_model.host_ip)
        container_node_info.setdefault('type', self.docker_model.component_type)
        container_node_info.setdefault('isUseIp', self.docker_model.use_ip)
        return container_node_info

    def __get_route_dicts(self, route_list=None):
        if route_list is None:
            return { 'false': 'route_list is None' }
        
        r_list = []
        for line in route_list:
            if ( line == '' ): continue
            route_ip = line.split()[1]
            netmask = line.split()[2]
            if ( len(route_ip.split(r'.')) != 4 or len(netmask.split(r'.')) !=4 ): continue
            route_info = {}
            route_info['route_ip'] = route_ip
            mask_num = _mask_to_num(netmask)
            if isinstance(mask_num, dict):
                return { 'false' : 'netmask Illegal: %s' % (mask_num['false']) }
            else:
                route_info['mask_num'] = mask_num
            route_info['dev'] = line.split()[7]
            if not route_info in r_list:
                r_list.append(route_info)
        return r_list


class Container_start_action(Abstract_Async_Thread):
    
    container_opers = Container_Opers()
    
    def __init__(self, container_name):
        super(Container_start_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin start')
            self.__issue_start_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_start_action(self):
        start_rst, start_flag = {}, {}
        logging.info('write start flag')
        start_flag = {'status': Status.starting, 'message':''}
        self.container_opers.write_container_status_by_containerName(self.container_name, start_flag)
        client = Client()
        client.start(self.container_name)
        stat = self.container_opers.get_container_stat(self.container_name)
        if stat == Status.stopped:
            message = 'start container %s failed' % self.container_name
        else:
            message = ''
        start_rst.setdefault('status', stat)
        start_rst.setdefault('message', message)
        logging.info('write start result')
        
        self.container_opers.write_container_status_by_containerName(self.container_name, start_rst)


class Container_stop_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    container_opers = Container_Opers()
    
    def __init__(self, container_name):
        super(Container_stop_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin stop')
            self.__issue_stop_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_stop_action(self):
        stop_rst, stop_flag = {}, {}
        logging.info('write stop flag')
        stop_flag = {'status':Status.stopping, 'message':''}
        self.container_opers.write_container_status_by_containerName(self.container_name, stop_flag)
        
        self.docker_opers.stop(self.container_name, 30)
        stat = self.container_opers.get_container_stat(self.container_name)
        if stat == Status.started:
            status = Status.failed
            message = 'stop container %s failed' % self.container_name
        else:
            status = Status.stopped
            message = ''
        stop_rst.setdefault('status', status)
        stop_rst.setdefault('message', message)
        logging.info('write stop result')
        self.container_opers.write_container_status_by_containerName(self.container_name, stop_rst)


class Container_destroy_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    container_opers = Container_Opers()
    
    def __init__(self, container_name):
        super(Container_destroy_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin destroy')
            self.__issue_destroy_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_destroy_action(self):
        """
            destroy container and remove docker mount dir data
        """

        destroy_rst = {}
        logging.info('write destroy flag')
        destroy_flag = {'status':Status.destroying, 'message':''}
        self.container_opers.write_container_status_by_containerName(self.container_name, destroy_flag)
        
        '''
           get mount dir first, otherwise get nothing where container removed~
        '''
        
        mount_dir_list = self.__get_delete_mount_dir()
        self.docker_opers.destroy(self.container_name)
        logging.info('container_name :%s' % str(self.container_name) )
        
        self.__remove_mount_dir(mount_dir_list)
            
        exists = self.container_opers.check_container_exists(self.container_name)
        
        if exists:
            message = 'destroy container %s failed' % self.container_name
            destroy_rst.setdefault('status', Status.failed)
            destroy_rst.setdefault('message', message)
            logging.error('destroy container %s failed' % self.container_name)
        else:
            destroy_rst.setdefault('status', Status.destroyed)
            destroy_rst.setdefault('message', '')
            
        self.container_opers.write_container_status_by_containerName(self.container_name, destroy_rst)

    def __remove_mount_dir(self, mount_dir_list):
        for mount_dir in mount_dir_list:
            os.system('rm -rf %s' % mount_dir)

    def __get_delete_mount_dir(self):
        mount_dir_list  = []
        _inspect = self.docker_opers.inspect_container(self.container_name)
        con = Container_Model(_inspect)
        volumes = con.inspect_volumes()
        for _, mount_dir in volumes.items():
            mount_dir_list.append(mount_dir)
        return mount_dir_list
        
