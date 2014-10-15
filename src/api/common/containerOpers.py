'''
Created on Sep 8, 2014

@author: root
'''
import logging
import traceback
import docker
import os, sys

from abstractContainerOpers import Abstract_Container_Opers
from abstractAsyncThread import Abstract_Async_Thread
from helper import *

class Container_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def issue_create_action(self, arg_dict):
        
        container_node_info = self._get_container_info(arg_dict)
        logging.info('get container info: %s' % str(container_node_info))
        
        create_result = self.create_container(arg_dict)
        
        if create_result:
            logging.info('create container successful, write info!')
            self.zkOper.write_container_node_info(container_node_info)
            return
        failed_container_name = arg_dict.get('container_name')
        return failed_container_name
        
    def create_container(self, arg_dict={}):
        
        logging.info('create_container args: %s' % str(arg_dict) )
        container_name = arg_dict.get('container_name')
        container_type = arg_dict.get('container_type')
        env = dict(arg_dict.get('env'))
        
        logging.info('container_name: %s' % container_name)
        logging.info('container_type: %s' % container_type)
        logging.info('env: %s' % str(env) )
        
        if container_type == 'mclusternode':
            mcluster_info = self.zkOper.retrieve_mcluster_info_from_config()
            version = mcluster_info.get('image_version')
            name = mcluster_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _ports = eval(mcluster_info.get('ports'))
            _mem_limit = mcluster_info.get('mem_limit')
            _volumes = dict(arg_dict.get('volumes'))
            _binds = dict( arg_dict.get('binds'))
            #_binds = self.__rewrite_bind_arg(container_name, binds)
        
        elif container_type == 'mclustervip':
            mclustervip_info = self.zkOper.retrieve_mclustervip_info_from_config()
            version = mclustervip_info.get('image_version')
            name = mclustervip_info.get('image_name')
            image_name = '%s:%s' % (name, version)
            _mem_limit = mclustervip_info.get('mem_limit')
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
        except:
            logging.error('the exception of creating container:%s' % str(traceback.format_exc()))
            return False
        
        result = self._check_create_status(container_name)
        if not result:
            logging.error('the exception of creating container')
            return False
        return True
    
    def _get_container_info(self, arg_dict):
        env = eval(arg_dict.get('env'))
        container_node_info= {}
        container_node_info.setdefault('containerClusterName', arg_dict.get('containerClusterName'))
        container_node_info.setdefault('containerNodeIP', arg_dict.get('container_ip'))
        container_node_info.setdefault('hostIp', arg_dict.get('host_ip'))
        container_node_info.setdefault('ipAddr', arg_dict.get('container_ip'))
        container_node_info.setdefault('containerName', arg_dict.get('container_name'))
        container_node_info.setdefault('mountDir', arg_dict.get('volumes'))
        container_node_info.setdefault('type', arg_dict.get('container_type'))
        container_node_info.setdefault('zookeeperId', env.get('ZKID'))
        container_node_info.setdefault('netMask', env.get('NETMASK'))
        container_node_info.setdefault('gateAddr', env.get('GATEWAY'))
        return container_node_info
    
    def _log_docker_run_command(self, env, _mem_limit, _volumes, container_name, image_name):
        
        cmd = ''
        cmd += 'docker run -i -t --rm --privileged -n --memory="%s" -h %s'  % (_mem_limit, container_name)
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
        cmd += '--env "N1_IP=%s" \n' % env.get('N1_IP')
        cmd += '--env "N1_HOSTNAME=%s" \n'% env.get('N1_HOSTNAME') 
        cmd += '--env "N2_IP=%s" \n' % env.get('N2_IP')
        cmd += '--env "N2_HOSTNAME=%s" \n' % env.get('N2_HOSTNAME')
        cmd += '--env "N3_IP=%s" \n' % env.get('N3_IP')
        cmd += '--env "N3_HOSTNAME=%s" \n' % env.get('N3_HOSTNAME')
        cmd += '--name %s %s' % (container_name, image_name)
        logging.info(cmd)
        
    def _check_create_status(self, container_name):
        flag = get_container_stat(container_name)
        if flag == 0:
            return True
        else:
            return False
    
    def __rewrite_bind_arg(self, container_name, bind_arg):
        re_bind_arg = {}
        for k,v in bind_arg.items():
            if '/srv/docker/vfs/dir' in k:
                _path = '/srv/docker/vfs/dir/%s' % container_name
                if not os.path.exists(_path):
                    os.mkdir(_path)
                re_bind_arg.setdefault(_path, v)
            else:
                re_bind_arg.setdefault(k, v)
        return re_bind_arg
    
    def stop(self, container_name):
        
        container_stop_action = Container_stop_action(container_name)
        container_stop_action.start()
    
    def start(self, container_name):
        logging.info('get work')
        container_start_action = Container_start_action(container_name)
        container_start_action.start()
    
    def destory(self, container_name):
        try:
            result = 0
            c = docker.Client('unix://var/run/docker.sock')
            c.kill(container_name)
            c.remove_container(container_name, force=True)
            flag = get_container_stat(container_name)
            if flag == 0:
                result = 'start container %s failed' % container_name
            elif flag == 2:
                result = 'container %s not exists!' % container_name
        except:
            result = str(traceback.format_exc())
            logging.error(result)
        finally:
            return result

    def check(self, container_name):
        result = {}
        container_operation_record = self.zkOper.retrieve_container_status(container_name)
        status = container_operation_record.get('status')
        message = container_operation_record.get('message')
        result.setdefault('status', status)
        result.setdefault('message', message)
        return result


class Container_start_action(Abstract_Async_Thread):
    
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
        self.zkOper.write_container_status(self.container_name, start_flag)
        
        c = docker.Client('unix://var/run/docker.sock')
        logging.info('container_name: %s' % self.container_name)
        c.start(self.container_name)
        flag = get_container_stat(self.container_name)
        if flag == 1:
            message = 'start container %s failed' % self.container_name
        else:
            message = ''
        start_rst['status'] = 'started'
        start_rst['message'] = message
        logging.info('write start result')
        self.zkOper.write_container_status(self.container_name, start_rst)
        
        
class Container_stop_action(Abstract_Async_Thread):
    
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
        self.zkOper.write_container_status(self.container_name, stop_flag)
        
        c = docker.Client('unix://var/run/docker.sock')
        logging.info('stop container: %s' % self.container_name)
        c.stop(self.container_name, 30)
        flag = get_container_stat(self.container_name)
        if flag == 0:
            message = 'start container %s failed' % self.container_name
        else:
            message = ''
        stop_rst['status'] = 'stopped'
        stop_rst['message'] = message
        logging.info('write stop result')
        self.zkOper.write_container_status(self.container_name, stop_rst)

