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
from docker.dockerOpers import Docker_Opers
from container.container_module import Container
from utils.exceptions import CommonException, RetryException
from utils.log import _log_docker_run_command
from utils import _is_ip, _is_mask, _mask_to_num, _check_create_status
from componentProxy.componentDockerModelFactory import ComponentDockerModelFactory

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
    
    def get_all_containers(self, all=True):
        """get all containers on some server
        
        all -> True  all containers on such server
        all -> False  started containers on such server
        """
        container_name_list = []
        container_info_list = self.docker_opers.containers(all)
        for container_info in container_info_list:
            name = container_info.get('Names')[0]
            name = name.replace('/', '')
            container_name_list.append(name)
        return container_name_list
    
    def check_container_exists(self, container_name):
        container_name_list = self.get_all_containers()
        return_result = container_name in container_name_list
        return return_result
    
    
class Container_create_action(object):
    
    docker_opers = Docker_Opers()
    
    component_docker_model_factory = ComponentDockerModelFactory()
    
    def __init__(self):
        '''
            constructor
        '''
        
    def create(self, arg_dict):
        if arg_dict is None or {} == arg_dict:
            raise CommonException("please check the param is not null![the code is container_opers's create method]")
        
        container_name = arg_dict.get('container_name')
        component_type = arg_dict.get('component_type')
        env = eval(arg_dict.get('env'))
        
        docker_model = self.component_docker_model_factory.create(component_type, arg_dict)
        
        _log_docker_run_command(env, docker_model)
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
        
        init_con_ret = self.__set_ip_add_route_retry(3, container_name)
        if not init_con_ret:
            error_message = '__set_ip_add_route_retry container failed'
            logging.error(error_message)
            raise CommonException(error_message)
        
        result = _check_create_status(container_name)
        if not result:
            error_message = 'the exception of creating container'
            logging.error(error_message)
            raise CommonException(error_message)
        
        container_node_info = self._get_container_info(container_name, arg_dict)
        logging.info('get container info: %s' % str(container_node_info))
        self.zkOper.write_container_node_info('started', container_node_info)
    
    def __set_ip_add_route_retry(self, retryCount, container_name=None):
        
        if container_name is None:
            return False
        
        ret = False
        
        for count in range(0,retryCount):
            while True:
                try:
                    self.__set_ip_add_route(container_name)
                except RetryException:
                    logging.info('__set_ip_add_route_retry container, try times :%s' % count)
                    continue
                
                ret = True
                break
            
        return ret
        
    def __set_ip_add_route(self, container_name=None):
        timeout = 5
        
        ip,mask = self.retrieve_container_ip_mark(container_name)
        
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
            if len(r_list) == 0:
                child.sendline(r"route add default gw %s" % (real_route))
                child.expect(["#", pexpect.EOF, pexpect.TIMEOUT], timeout)
                child.sendline(r"")
            elif len(r_list) > 1 or r_list[0]['route_ip'] != real_route:
                raise RetryException("error")
            else:
                raise RetryException("error")
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
        
        
    def _get_container_info(self, container_name, arg_dict):
        con = Container(container_name)
        container_node_info= {}
        container_node_info.setdefault('containerName', container_name)
        container_node_info.setdefault('inspect', con.inspect)
        container_node_info.setdefault('hostIp', arg_dict.get('host_ip'))
        container_node_info.setdefault('type', arg_dict.get('container_type'))
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
    
    docker_opers = Docker_Opers()
    
    def __init__(self, container_name):
        super(Container_start_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin __start')
            self.__issue_start_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_start_action(self):
        start_rst, start_flag = {}, {}
        logging.info('write __start flag')
        start_flag = {'status':'starting', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, start_flag)
        self.docker_opers.__start(self.container_name)
        stat = self.docker_opers.get_container_stat(self.container_name)
        if stat == 'stopped':
            message = '__start container %s failed' % self.container_name
        else:
            message = ''
        start_rst.setdefault('status', stat)
        start_rst.setdefault('message', message)
        logging.info('write __start result')
        '''
        @todo:
        1. check the duplicate with above code? same as write_container_status_by_containerName
        '''
        self.zkOper.write_container_status_by_containerName(self.container_name, start_rst)

        
class Container_stop_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    
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
        stat = self.docker_opers.get_container_stat(self.container_name)
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
