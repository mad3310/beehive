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
from utils.exceptions import UserVisiableException
from componentProxy import _mount_dir


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
        self.cpuacct_stat_path = '/cgroup/cpuacct/lxc/%s/cpuacct.stat' % self.container_id
        self.cpushares_path = '/cgroup/cpu/lxc/%s/cpu.shares' % self.container_id
        self.cpuset_path = '/cgroup/cpu/lxc/%s/cpuset.cpus' % self.container_id
        self.disk_bps= '/cgroup/blkio/lxc/%s/blkio.throttle.%%s_bps_device' % self.container_id
        self.disk_iops= '/cgroup/blkio/lxc/%s/blkio.throttle.%%s_iops_device' % self.container_id

    def get_container_id(self):
        _inspect = self.docker_opers.inspect_container(self.container_name)
        con = Container_Model(_inspect)
        return con.id()

    def get_file_value(self, file_path):
        value = ''
        file_cmd = 'cat %s' % file_path
        if os.path.exists(file_path):
            value = commands.getoutput(file_cmd)
        return value

    def echo_value_to_file(self, value, file_path):
        cmd = 'echo %s > %s' % (value, file_path)
        logging.info('run cmd :%s' % cmd)
        commands.getoutput(cmd)
        return self.get_file_value(file_path) == str(value)

    def get_con_used_mem(self):
        return float(self.get_file_value(self.used_mem_path))

    def get_con_used_memsw(self):
        return float(self.get_file_value(self.used_memsw_path))

    def get_con_limit_mem(self):
        return float(self.get_file_value(self.limit_mem_path))

    def get_con_limit_memsw(self):
        return float(self.get_file_value(self.limit_memsw_path))

    def get_cpuacct_stat_value(self):
        value = self.get_file_value(self.cpuacct_stat_path)
        return value.split('\n')

    def get_cpushares_value(self):
        return self.get_file_value(self.cpushares_path)

    def get_cpuset_value(self):
        return self.get_file_value(self.cpuset_path)

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

    def __extend_memsw(self, times):
        memsw_value = self.get_con_limit_memsw()
        extend_value = int(memsw_value)*int(times)
        if not self.echo_value_to_file(extend_value, self.limit_memsw_path):
            raise UserVisiableException('extend container: %s memroy swap faild, please check!' % self.container_name)
        return extend_value

    def __extend_mem(self, times):
        mem_value = self.get_con_limit_mem()
        extend_value = int(mem_value)*int(times)
        if not self.echo_value_to_file(extend_value, self.limit_mem_path):
            raise UserVisiableException('extend container: %s memory faild, please check!' % self.container_name)
        return extend_value

    def extend_memory(self, times):
        memsw_ret = self.__extend_memsw(times)
        mem_ret = self.__extend_mem(times)
        return memsw_ret and mem_ret

    def set_cpushares(self, cpushares="1024"):
        if not self.echo_value_to_file(cpushares, self.cpushares_path):
            raise UserVisiableException('set container :%s cpu.shares value:% failed' % (self.container_name, cpushares))
        return self.get_cpushares_value()

    def set_cpuset(self, cpus):
        if not self.echo_value_to_file(cpus, self.cpuset_path):
            raise UserVisiableException('set container :%s cpus value:%s failed' % (self.container_name, cpus))
        return self.get_cpuset_value()

    def set_container_disk_bps(self, _type, method='write', data=0):
        mount_dir = _mount_dir.get(_type, '/srv')
        dev_number = self.get_dev_number_by_mount_dir(mount_dir)
        value = '%s\t%d' % (dev_number, data)
        path = self.disk_bps % method
        self.echo_value_to_file(value, path)
        return value

    def set_container_disk_iops(self, _type, method='write', times=0):
        mount_dir = _mount_dir.get(_type, '/srv')
        dev_number = self.get_dev_number_by_mount_dir(mount_dir)
        value = '%s\t%d' % (dev_number, times)
        path = self.disk_iops % method
        self.echo_value_to_file(value, path)
        return value

    @staticmethod
    def get_dev_number_by_mount_dir(mount_dir):
        device_cmd = """ls -l `df -P | grep %s | awk '{print $1}'` | awk -F"/" '{print $NF}'""" % mount_dir
        device = commands.getoutput(device_cmd)
        
        #device mapper works well 
        if not device.startswith('dm'): 
            device = re.sub('\d+', '', device) 
        
        device_path = '/dev/%s' % device
        if not os.path.exists(device_path):
            raise UserVisiableException('device :%s not exist! maybe get wrong path' % device_path)
        dev_number_cmd = """ls -l %s | awk '{print $5$6}' | awk -F "," '{print $1":"$2}'""" % device_path
        dev_num = commands.getoutput(dev_number_cmd)
        if not re.match("\d+\:\d+", dev_num):
            raise UserVisiableException('get device number wrong :%s' % dev_num)
        return dev_num
