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
import re

from common.abstractContainerOpers import Abstract_Container_Opers
from common.abstractAsyncThread import Abstract_Async_Thread
from docker_letv.dockerOpers import Docker_Opers
from container.container_module import Container
from utils.exceptions import CommonException, RetryException
from utils.log import _log_docker_run_command
from utils import _is_ip, _is_mask, _mask_to_num
from zk.zkOpers import ZkOpers
from docker import Client


class Container_Opers(Abstract_Container_Opers):
    
    docker_opers = Docker_Opers()
    
    def __init__(self):
        '''
        Constructor
        '''
        
    def create(self, arg_dict={}):
        container_create_action = Container_create_action()
        container_create_action.create(arg_dict)
   
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
        result = {}
        container_operation_record = self.zkOper.retrieve_container_status_from_containerName(container_name)
        status = container_operation_record.get('status')
        message = container_operation_record.get('message')
        result.setdefault('status', status)
        result.setdefault('message', message)
        return result
    
    def get_container_stat(self, container_name):
        """
        """
        exists = self.check_container_exists(container_name)
        if not exists:
            return 'destroyed'
        
        container_info_list = self.docker_opers.containers(all=True)
        
        for container_info in container_info_list:
            name = container_info.get('Names')[0]
            name = name.replace('/', '')
            if name == container_name:
                stat = container_info.get('Status')
                if 'Up' in stat:
                    return 'started'
                elif 'Exited' in stat:
                    return 'stopped'

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
    
'''
@todo: need to check if the async? or sync? extend object?
'''    
class Container_create_action(object):
    
    docker_opers = Docker_Opers()
    container_opers = Container_Opers()
    zkOper = ZkOpers()
        
    def __init__(self):
        '''
            constructor
        '''
    
    def create(self, docker_model):
        
        _log_docker_run_command(docker_model)
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
        self.docker_opers.create(docker_model)
        
        '''
        orginal:
            container_name, 
            privileged=True, 
            network_mode='bridge', 
            binds=_binds
        '''
        self.docker_opers.start(docker_model)
        
        '''
        @todo: need to open these code
        '''
#         if docker_model.use_ip:
#             init_con_ret = self.set_ip_add_route_retry(3, container_name)
#             if not init_con_ret:
#                 error_message = 'set_ip_add_route_retry container failed'
#                 logging.error(error_message)
#                 raise CommonException(error_message)
        
        result = self.__check_create_status(docker_model)
        if not result:
            error_message = 'the exception of creating container'
            logging.error(error_message)
            raise CommonException(error_message)
        
        container_node_info = self._get_container_info(docker_model)
        logging.info('get container info: %s' % str(container_node_info))
        self.zkOper.write_container_node_info('started', container_node_info)

    def __check_create_status(self, docker_model):
        container_name = docker_model.name
        stat = self.container_opers.get_container_stat(container_name)
        if stat == 'started':
            return True
        else:
            return False

    def set_ip_add_route_retry(self, retryCount, container_name=None):
        
        if container_name is None:
            return False
        
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
        
        ip,mask = self.__retrieve_container_ip_mask(container_name)
        
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
    
    '''
    @todo: 
    1. check the duplicate with Container's logic? can be remove?
    '''
    def __retrieve_container_ip_mask(self, container_name):
        re_info = self.docker_opers.inspect_container(container_name)
        for env in re_info['Config']['Env']:
            if re.match(r"^IP=", env):
                key, ip = re.split(r"=", env)
            if re.match(r"^NETMASK=", env):
                key, mask = re.split(r"=", env)
                
        if not _is_ip(ip):
            error_message = "get IP error: %s" % ip
            logging.error(error_message)
            raise RetryException(error_message)
        
        if not _is_mask(mask):
            error_message = "get MASK error: %s" % mask
            logging.error(error_message)
            raise RetryException(error_message)
        
        return ip,mask
        
    def _get_container_info(self, docker_model):
        container_name = docker_model.name
        con = Container(container_name)
        container_node_info= {}
        container_node_info.setdefault('containerName', container_name)
        container_node_info.setdefault('inspect', con.inspect)
        container_node_info.setdefault('hostIp', docker_model.host_ip)
        container_node_info.setdefault('type', docker_model.component_type)
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
        start_flag = {'status':'starting', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, start_flag)
        client = Client()
        client.start(self.container_name)
        stat = self.container_opers.get_container_stat(self.container_name)
        if stat == 'stopped':
            message = 'start container %s failed' % self.container_name
        else:
            message = ''
        start_rst.setdefault('status', stat)
        start_rst.setdefault('message', message)
        logging.info('write start result')
        '''
        @todo:
        1. check the duplicate with above code? same as write_container_status_by_containerName
        '''
        self.zkOper.write_container_status_by_containerName(self.container_name, start_rst)

        
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
        stop_flag = {'status':'stopping', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, stop_flag)
        
        self.docker_opers.stop(self.container_name, 30)
        stat = self.container_opers.get_container_stat(self.container_name)
        if stat == 'started':
            status = 'failed'
            message = 'stop container %s failed' % self.container_name
        else:
            status = 'stopped'
            message = ''
        stop_rst.setdefault('status', status)
        stop_rst.setdefault('message', message)
        logging.info('write stop result')
        '''
        @todo:
        1. check the duplicate with above code? same as write_container_status_by_containerName
        '''
        self.zkOper.write_container_status_by_containerName(self.container_name, stop_rst)


class Container_destroy_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    
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

        destroy_rst, destroy_flag = {}, {}
        logging.info('write destroy flag')
        destroy_flag = {'status':'destroying', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, destroy_flag)
        mount_dir = self.__get_normal_node_mount_dir()
        self.docker_opers.destroy(self.container_name)
        logging.info('container_name :%s' % str(self.container_name) )
        logging.info('mount_dir :%s' % str(mount_dir) )
        if os.path.exists(mount_dir):
            os.system('rm -rf %s' % mount_dir)
            
        exists = self.docker_opers.check_container_exists(self.container_name)
        
        if exists:
            message = 'destroy container %s failed' % self.container_name
            destroy_rst.setdefault('status', 'failed')
            destroy_rst.setdefault('message', message)
            logging.error('destroy container %s failed' % self.container_name)
        else:
            destroy_rst.setdefault('status', 'destroyed')
            destroy_rst.setdefault('message', '')
            
        '''
        @todo:
        1. check the duplicate with above code? same as write_container_status_by_containerName
        '''
        self.zkOper.write_container_status_by_containerName(self.container_name, destroy_rst)

    def __get_normal_node_mount_dir(self):
        mount_dir = ''
        con = Container(self.container_name)
        type = con.type()
        '''
        @todo: if other component need to delete these volumn?
        '''
        if 'vip' in type:
            logging.info('vip node, no need to remove mount dir!')
        else:
            '''
            @todo: 
            1. remove the directory is right? is this directory when create container?
            '''
            volumes = con.volumes()
            mount_dir = volumes.get('/srv/mcluster')
            if not mount_dir:
                mount_dir = ''
        return mount_dir


class ContainerLoad(object):

    def __init__(self, container_name):
        self.container_name = container_name
        self.container_id = ''
        if not self.container_id:
            self.container_id = self.get_container_id()
        self.used_mem_path = '/cgroup/memory/lxc/%s/memory.usage_in_bytes' % self.container_id
        self.limit_mem_path = '/cgroup/memory/lxc/%s/memory.limit_in_bytes' % self.container_id
        self.used_memsw_path = '/cgroup/memory/lxc/%s/memory.memsw.usage_in_bytes' % self.container_id
        self.limit_memsw_path = '/cgroup/memory/lxc/%s/memory.memsw.limit_in_bytes' % self.container_id
        self.under_oom_path = '/cgroup/memory/lxc/%s/memory.oom_control' % self.container_id
        self.root_mnt_path = '/srv/docker/devicemapper/mnt/%s' % self.container_id
        self.memory_stat_path = '/cgroup/memory/lxc/%s/memory.stat' % self.container_id
        self.cpuacct_stat_path = '/cgroup/cpuacct/lxc/%s/cpuacct.stat' % self.container_id
        
    def get_container_id(self):
        con = Container(self.container_name)
        return con.id()

    def get_file_value(self, file_path):
        value = 0
        file_cmd = 'cat %s' % file_path
        if os.path.exists(file_path):
            value = commands.getoutput(file_cmd)
        return value

    def echo_value_to_file(self, value, file_path):
        cmd = 'echo %s > %s' % (value, file_path)
        commands.getoutput(cmd)
        return self.get_file_value(file_path) == str(value)

    def get_dir_size(self, dir_path):
        size = 0
        dir_cmd = 'du -sm %s' % dir_path
        if os.path.exists(dir_path):
            value = commands.getoutput(dir_cmd)
            if value:
                size = re.findall('(.*)\\t.*', value)[0]
        else:
            logging.info('path %s not exist, may be VIP node' % dir_path)
        return size

    def get_con_used_mem(self):
        return float(self.get_file_value(self.used_mem_path) )

    def get_con_used_memsw(self):
        return float(self.get_file_value(self.used_memsw_path) )

    def get_con_limit_mem(self):
        return float(self.get_file_value(self.limit_mem_path))

    def get_con_limit_memsw(self):
        return float(self.get_file_value(self.limit_memsw_path))

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
        
        if used_mem and limit_mem:
            mem_load_rate =  used_mem / limit_mem
            mem_load_dict.setdefault('used_mem', used_mem)
            mem_load_dict.setdefault('limit_mem', limit_mem)
            mem_load_dict.setdefault('mem_load_rate', mem_load_rate)
        return mem_load_dict

    def get_memsw_load(self):
        memsw_load_rate, memsw_load_dict = 0, {}
        used_memsw = self.get_con_used_memsw()
        limit_memsw = self.get_con_limit_memsw()
        
        if used_memsw and limit_memsw:
            memsw_load_rate =  used_memsw / limit_memsw
            memsw_load_dict.setdefault('used_memsw', used_memsw)
            memsw_load_dict.setdefault('limit_memsw', limit_memsw)
            memsw_load_dict.setdefault('memsw_load_rate', memsw_load_rate)
        return memsw_load_dict    

    def get_root_mnt_size(self):
        return self.get_dir_size(self.root_mnt_path)

    def get_mysql_mnt_size(self):
        mysql_mnt_path = ''
        con = Container(self.container_name)
        volumes = con.volumes()
        type = con.type()
        if volumes:
            mysql_mnt_path = volumes.get('/srv/mcluster')
            return self.get_dir_size(mysql_mnt_path)
        elif type == 'mclustervip':
            logging.info('VIP node, no mysql mount~')
            return 0

    def get_sum_disk_load(self):
        root_mnt_size = self.get_root_mnt_size()
        mysql_mnt_size = self.get_mysql_mnt_size()
        return root_mnt_size, mysql_mnt_size

    def double_memsw_size(self):
        memsw_value = self.get_con_limit_memsw()
        double_value = int(memsw_value)*2
        return self.echo_value_to_file(double_value, self.limit_memsw_path)

    def double_mem_size(self):
        mem_value = self.get_con_limit_mem()
        double_value = int(mem_value)*2
        return self.echo_value_to_file(double_value, self.limit_mem_path)

    def double_mem(self):
        memsw_ret = self.double_memsw_size()
        mem_ret = self.double_mem_size()
        return mem_ret and mem_ret
