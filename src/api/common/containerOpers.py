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
import docker

from abstractContainerOpers import Abstract_Container_Opers
from abstractAsyncThread import Abstract_Async_Thread
from dockerOpers import Docker_Opers
from container_module import Container
from helper import *
from resourceOpers import Res_Opers

class Container_Opers(Abstract_Container_Opers):
    
    docker_opers = Docker_Opers()
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def issue_create_action(self, arg_dict):
        
        create_result = self.create(arg_dict)
        if create_result:
            logging.info('create container successful, write info!')
            return
        failed_container_name = arg_dict.get('container_name')
        return failed_container_name
        
    def create(self, arg_dict={}):
        
        logging.info('create_container args: %s' % str(arg_dict) )
        container_name = arg_dict.get('container_name')
        container_type = arg_dict.get('container_type')
        containerClusterName = arg_dict.get('containerClusterName')
        container_ip = arg_dict.get('container_ip')
        env = eval(arg_dict.get('env'))
        
        logging.info('container_name: %s' % container_name)
        logging.info('container_type : %s' % container_type)
        logging.info('env: %s' % str(env) )
        
        if container_type == 'mclusternode':
            mcluster_info = self.zkOper.retrieve_mcluster_info_from_config()
            version = mcluster_info.get('image_version')
            name = mcluster_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _ports = eval(mcluster_info.get('ports'))
            _mem_limit = int( mcluster_info.get('mem_limit') )
            #_mem_limit = mcluster_info.get('mem_limit')
            _volumes = eval(arg_dict.get('volumes'))
            _binds = eval( arg_dict.get('binds'))
            _binds = self.__rewrite_bind_arg(containerClusterName, _binds)
            logging.info('_binds : %s' % str(_binds))
        
        elif container_type == 'mclustervip':
            mclustervip_info = self.zkOper.retrieve_mclustervip_info_from_config()
            version = mclustervip_info.get('image_version')
            name = mclustervip_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _mem_limit = int( mclustervip_info.get('mem_limit') )
            #_mem_limit = mclustervip_info.get('mem_limit')
            _binds, _ports, _volumes = None, None, None
        
        logging.info('_volumes:%s' % str(_volumes))
        logging.info('_binds:%s' % str(_binds))
        logging.info('_ports:%s' % str(_ports))
        self._log_docker_run_command(env, _mem_limit, _volumes, container_name, image_name)
        try:
            c = docker.Client('unix://var/run/docker.sock')
            container_id = c.create_container(image=image_name, hostname=container_name, user='root',
                                              name=container_name, environment=env, tty=True, ports=_ports, stdin_open=True,
                                              mem_limit=_mem_limit, volumes=_volumes)
            c.start(container_name, privileged=True, network_mode='bridge', binds=_binds)
            init_con_ret = init_container(container_name)
        except:
            logging.error('the exception of creating container:%s' % str(traceback.format_exc()))
            return False
        
        if not init_con_ret:
            logging.error('init container failed')
            return False            
        
        result = self._check_create_status(container_name)
        if not result:
            logging.error('the exception of creating container')
            return False
        container_node_info = self._get_container_info(container_name, arg_dict)
        logging.info('get container info: %s' % str(container_node_info))
        self.zkOper.write_container_node_info('started', container_node_info)
        return True
    
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
   
    def _get_container_info(self, container_name, arg_dict):
        con = Container(container_name)
        container_node_info= {}
        container_node_info.setdefault('container_name', container_name)
        container_node_info.setdefault('inspect', con.inspect)
        container_node_info.setdefault('host_ip', arg_dict.get('host_ip'))
        container_node_info.setdefault('type', arg_dict.get('container_type'))
        return container_node_info
    
    def _log_docker_run_command(self, env, _mem_limit, _volumes, container_name, image_name):
        
        cmd = ''
        cmd += 'docker run -i -t --rm --privileged -n --memory="%s" -h %s'  % (_mem_limit, container_name)
        if _volumes:
            for host_addr, container_addr in _volumes.items():
                if container_addr:
                    cmd += ' -v %s:%s \n' % (host_addr, container_addr)
                else:
                    cmd += ' -v %s \n' % host_addr
        
        cmd += '--env "ZKID=%s" \n' % env.get('ZKID')
        cmd += '--env "IP=%s" \n' % env.get('IP')
        cmd += '--env "HOSTNAME=%s" \n' % env.get('HOSTNAME')
        cmd += '--env "NETMASK=%s" \n' % env.get('NETMASK')
        cmd += '--env "GATEWAY=%s" \n' % env.get('GATEWAY')
        N1_IP = env.get('N1_IP')
        if N1_IP:
            cmd += '--env "N1_IP=%s" \n' % N1_IP
        N1_HOSTNAME = env.get('N1_HOSTNAME')
        if N1_HOSTNAME:
            cmd += '--env "N1_HOSTNAME=%s" \n' % N1_HOSTNAME
        N2_IP = env.get('N2_IP')
        if N2_IP:
            cmd += '--env "N2_IP=%s" \n' % N2_IP
        N2_HOSTNAME = env.get('N2_HOSTNAME')
        if N2_HOSTNAME:
            cmd += '--env "N2_HOSTNAME=%s" \n' % N2_HOSTNAME 
        N3_IP = env.get('N3_IP')
        if N3_IP:
            cmd += '--env "N3_IP=%s" \n' % N3_IP 
        N3_HOSTNAME = env.get('N3_HOSTNAME')
        if N3_HOSTNAME:
            cmd += '--env "N3_HOSTNAME=%s" \n' % N3_HOSTNAME 
        cmd += '--name %s %s' % (container_name, image_name)
        logging.info(cmd)
        
    def _check_create_status(self, container_name):
        stat = get_container_stat(container_name)
        if stat == 'started':
            return True
        else:
            return False
    
    def __rewrite_bind_arg(self, containerClusterName, bind_arg):
        re_bind_arg = {}
        for k,v in bind_arg.items():
            if '/data/mcluster_data' in k:
                _path = '/data/mcluster_data/d-mcl-%s' % containerClusterName
                if not os.path.exists(_path):
                    os.mkdir(_path)
                re_bind_arg.setdefault(_path, v)
            else:
                re_bind_arg.setdefault(k, v)
        return re_bind_arg

    def get_disk_load(self, container_name):
        res_opers = Res_Opers(container_name)
        return res_opers.get_container_disk_load()


class Container_start_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    
    def __init__(self, container_name):
        super(Container_start_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin start')
            self._issue_start_action()
        except:
            logging.error(traceback.format_exc())
            self.threading_exception_queue.put(sys.exc_info())

    def _issue_start_action(self):
        start_rst, start_flag = {}, {}
        logging.info('write start flag')
        start_flag = {'status':'starting', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, start_flag)
        self.docker_opers.start(self.container_name)
        stat = get_container_stat(self.container_name)
        if stat == 'stopped':
            message = 'start container %s failed' % self.container_name
        else:
            message = ''
        start_rst.setdefault('status', stat)
        start_rst.setdefault('message', message)
        logging.info('write start result')
        self.zkOper.write_container_status_by_containerName(self.container_name, start_rst)

        
class Container_stop_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    
    def __init__(self, container_name):
        super(Container_stop_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin stop')
            self._issue_stop_action()
        except:
            logging.error(traceback.format_exc())
            self.threading_exception_queue.put(sys.exc_info())

    def _issue_stop_action(self):
        stop_rst, stop_flag = {}, {}
        logging.info('write stop flag')
        stop_flag = {'status':'stopping', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, stop_flag)
        
        self.docker_opers.stop(self.container_name, 30)
        stat = get_container_stat(self.container_name)
        if stat == 'started':
            status = 'failed'
            message = 'stop container %s failed' % self.container_name
        else:
            status = 'stopped'
            message = ''
        stop_rst.setdefault('status', status)
        stop_rst.setdefault('message', message)
        logging.info('write stop result')
        self.zkOper.write_container_status_by_containerName(self.container_name, stop_rst)


class Container_destroy_action(Abstract_Async_Thread):
    
    docker_opers = Docker_Opers()
    
    def __init__(self, container_name):
        super(Container_destroy_action, self).__init__()
        self.container_name = container_name
        
    def run(self):
        try:
            logging.info('begin destroy')
            self._issue_destroy_action()
        except:
            logging.error(traceback.format_exc())
            self.threading_exception_queue.put(sys.exc_info())

    def _issue_destroy_action(self):
        """destroy container and remove docker mount dir data
        
        """

        destroy_rst, destroy_flag = {}, {}
        logging.info('write destroy flag')
        destroy_flag = {'status':'destroying', 'message':''}
        self.zkOper.write_container_status_by_containerName(self.container_name, destroy_flag)
        mount_dir = ''
        mount_dir = self._get_normal_node_mount_dir()
        self.docker_opers.destroy(self.container_name)
        logging.info('container_name :%s' % str(self.container_name) )
        logging.info('mount_dir :%s' % str(mount_dir) )
        if os.path.exists(mount_dir):
            os.system('rm -rf %s' % mount_dir)
        exists = check_container_exists(self.container_name)
        if exists:
            message = 'destroy container %s failed' % self.container_name
            destroy_rst.setdefault('status', 'failed')
            destroy_rst.setdefault('message', message)
            logging.error('destroy container %s failed' % self.container_name)
        else:
            destroy_rst.setdefault('status', 'destroyed')
            destroy_rst.setdefault('message', '')

        self.zkOper.write_container_status_by_containerName(self.container_name, destroy_rst)
    
    def _get_normal_node_mount_dir(self):
        mount_dir = ''
        if 'vip' not in self.container_name: 
            con_inspect = self.docker_opers.inspect_container(self.container_name)
            logging.info('inspect:%s, type:%s' % (con_inspect, type(con_inspect)) )
            mount_dir = con_inspect.get('Volumes').get('/srv/mcluster')
            if not mount_dir:
                mount_dir = ''
        return mount_dir
