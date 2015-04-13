'''
Created on Apr 5, 2015

@author: root
'''
import os
import commands
import re
import logging

from utils.invokeCommand import InvokeCommand
from docker_letv.dockerOpers import Docker_Opers
from container.container_model import Container_Model
from tornado.options import options

class StateOpers(object):
    
    docker_opers = Docker_Opers()

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
        _inspect = self.docker_opers.inspect_container(self.container_name)
        con = Container_Model(_inspect)
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
        return float(self.get_file_value(self.used_mem_path))

    def get_con_used_memsw(self):
        return float(self.get_file_value(self.used_memsw_path))

    def get_con_limit_mem(self):
        return float(self.get_file_value(self.limit_mem_path))

    def get_con_limit_memsw(self):
        return float(self.get_file_value(self.limit_memsw_path))

    def get_under_oom_value(self): 
        value = self.get_file_value(self.under_oom_path)
        under_oom_value = re.findall('.*under_oom (\d)$', value)[0]
        return int(under_oom_value)

    def get_memory_stat_value(self):
        value = self.get_file_value(self.memory_stat_path)
        return value.split('\n')

    def get_cpuacct_stat_value(self):
        value = self.get_file_value(self.cpuacct_stat_path)
        return value.split('\n')

    def get_memory_stat_item(self):
        mem_stat_dict = {}
        mem_stat_items = self.get_memory_stat_value()
        for item in mem_stat_items:
            if 'total_rss' in item:
                total_rss = item.split(' ')[1]
                mem_stat_dict.setdefault('total_rss', total_rss)
            elif 'total_swap ' in item:
                total_swap = item.split(' ')[1]
                mem_stat_dict.setdefault('total_swap', total_swap)
            elif 'total_cache ' in item:
                total_cache = item.split(' ')[1]
                mem_stat_dict.setdefault('total_cache', total_cache)
        return mem_stat_dict

    def get_cpuacct_stat_item(self):
        cpuacct_stat_dict = {}
        cpuacct_stat_items = self.get_cpuacct_stat_value()
        for item in cpuacct_stat_items:
            if 'user' in item:
                user = item.split(' ')[1]
                cpuacct_stat_dict.setdefault('user', user)
            elif 'system ' in item:
                system = item.split(' ')[1]
                cpuacct_stat_dict.setdefault('system', system)
        return cpuacct_stat_dict

    def get_network_io(self):
        network_io_dict, RX_SUM, TX_SUM = {}, 0, 0
        ivk_cmd = InvokeCommand()
        cmd = "sh %s %s" % (options.network_io_sh, self.container_id)
        content = ivk_cmd._runSysCmd(cmd)[0]
        RTX_list = re.findall('.*peth0\s+\d+\s+\d+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+(\d+).*', content)
        for RX, TX in RTX_list:
            RX_SUM += int(RX)
            TX_SUM += int(TX)
        network_io_dict.setdefault('RX', int(RX_SUM/1024/1024))
        network_io_dict.setdefault('TX', int(TX_SUM/1024/1024))
        return network_io_dict

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
        _inspect = self.docker_opers.inspect_container(self.container_name)
        con = Container_Model(_inspect)
        volumes = con.inspect_volumes()
        if volumes:
            mysql_mnt_path = volumes.get('/srv/mcluster')
            return self.get_dir_size(mysql_mnt_path)

    def get_sum_disk_load(self):
        root_mnt_size = self.get_root_mnt_size()
        mysql_mnt_size = self.get_mysql_mnt_size()
        return root_mnt_size, mysql_mnt_size

    def __double_memsw_size(self):
        memsw_value = self.get_con_limit_memsw()
        double_value = int(memsw_value)*2
        return self.echo_value_to_file(double_value, self.limit_memsw_path)

    def __double_mem_size(self):
        mem_value = self.get_con_limit_mem()
        double_value = int(mem_value)*2
        return self.echo_value_to_file(double_value, self.limit_mem_path)

    def double_mem(self):
        memsw_ret = self.__double_memsw_size()
        mem_ret = self.__double_mem_size()
        return mem_ret and mem_ret