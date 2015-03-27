#!/usr/bin/env python 2.6.6

import logging
import datetime
import traceback

from tornado.options import options
from abc import abstractmethod
from zk.zkOpers import ZkOpers
from resource_letv.ipOpers import IpOpers
from server.serverOpers import Server_Opers
from utils import _retrieve_userName_passwd
from utils.autoutil import *

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class CheckStatusBase(object):
    
    zkOper = ZkOpers()
    
    def __init__(self):
        if self.__class__ == CheckStatusBase:
            raise NotImplementedError, \
            "Cannot create object of class CheckStatusBase"
    
    @abstractmethod
    def check(self, data_node_info_list):
        raise NotImplementedError, "Cannot call abstract method"
    
    @abstractmethod
    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        raise NotImplementedError, "Cannot call abstract method"

    def write_status(self, total_count, success_count, failed_count, alarm_level, error_record, monitor_type, monitor_key):
        logging.info('write status!')
        result_dict = {}
        format_str = "total=%s, success count=%s, failed count=%s"
        format_values = (total_count, success_count, failed_count)
        message = format_str % format_values
        dt = datetime.datetime.now()
        result_dict.setdefault("message", message)
        result_dict.setdefault("alarm", alarm_level)
        result_dict.setdefault("error_record", error_record)
        result_dict.setdefault("ctime", dt.strftime(TIME_FORMAT))
        
        logging.info("monitor_type:" + monitor_type + " monitor_key:" + \
                     monitor_key + " monitor_value:" + str(result_dict))
        self.zkOper.write_monitor_status(monitor_type, monitor_key, result_dict)

    def _get(self, uri):
        rst = {}
        host_ip = getHostIp()
        logging.info('host ip :%s' % host_ip)
        adminUser, adminPasswd = _retrieve_userName_passwd()
        url = 'http://%s:%s%s' % (host_ip, options.port, uri)
        logging.info('get url :%s' % url)
        ret = http_get(url, _connect_timeout=40.0, _request_timeout=40.0, auth_username = adminUser, auth_password = adminPasswd)
        return ret.get('response')

class CheckResIpNum(CheckStatusBase):
    ip_opers = IpOpers()

    def check(self):
        try:
            monitor_type, monitor_key, error_record = 'res', 'ip_num', ''
            success_count = 0
            success_count = self.ip_opers.get_ip_num()
            if success_count < 20:
                error_record = 'the number of ips in ip Pool is %s, please add ips!' % success_count
            alarm_level = self.retrieve_alarm_level(0, success_count, 0)
            super(CheckResIpNum, self).write_status(0, success_count, 0, \
                                                        alarm_level, error_record, 
                                                        monitor_type, monitor_key)
        
        except:
            logging.error( str(traceback.format_exc()) )

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if 20 < success_count:
            return options.alarm_nothing
        elif 15 < success_count <= 20:
            return options.alarm_general
        else:
            return options.alarm_serious


class CheckResIpUsable(CheckStatusBase):
    
    ip_opers = IpOpers()
    
    def check(self):
        monitor_type, monitor_key, error_record = 'res', 'ip_usable', []
        failed_count = 0
        try:
            logging.info('do get_illegal_ips')
            error_record = self.ip_opers.get_illegal_ips(20)
            failed_count = len(error_record)
#            if failed_count:
#                 for ip in unusable_ip_list:
#                     error_record += 'ip: %s,' % str(ip)
            logging.info('check ip res resutl failed_count : %s' % failed_count)
        except:
            
            error_msg = str(traceback.format_exc())
            logging.error(error_msg)
            failed_count = 1
            error_record.append(error_msg)
            
            
        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        super(CheckResIpUsable, self).write_status(0, 0, \
                                                    failed_count, \
                                                    alarm_level, error_record, monitor_type, \
                                                    monitor_key)
        
    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious


class CheckContainersUnderOom(CheckStatusBase):
    
    server_opers = Server_Opers()
    
    def check(self):
        monitor_type, monitor_key, error_record = 'container', 'under_oom', []
        failed_count, containers_mem_load = 0, {}
        try:
            containers_under_oom = {}
            logging.info('do check under_oom')
            containers_under_oom = self._get('/monitor/serverCluster/containers/under_oom')
            logging.info('containers_under_oom:%s' % str(containers_under_oom) )
            
            for host_ip, host_cons_under_oom in containers_under_oom.items():
                for key, illegal_cons in host_cons_under_oom.items():
                    if illegal_cons:
                        each = {}
                        failed_count += len(illegal_cons)
                        each.setdefault(host_ip, illegal_cons)
                        error_record.append(each)
        
        except:
            
            error_msg = str(traceback.format_exc())
            logging.error(error_msg)
            failed_count = 1
            error_record.append(error_msg)
        
        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        super(CheckContainersUnderOom, self).write_status(0, 0, failed_count, 
                                                          alarm_level, error_record,
                                                          monitor_type, monitor_key)      

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious


class CheckContainersMemLoad(CheckStatusBase):

    server_opers = Server_Opers()

    def check(self):
        monitor_type, monitor_key, error_record = 'container', 'mem_load', []
        failed_count, containers_mem_load = 0, {}
        try:
            logging.info('do monitor memory load')
            containers_mem_load = self._get('/monitor/serverCluster/containers/memory')
            logging.info('containers_mem_load result:%s' % str(containers_mem_load) )
            overload_containers = self.__get_host_overload_containers(containers_mem_load)
            
            logging.info('load memory:%s' % str(overload_containers) )
            
            for host_ip, host_cons_mem_load in overload_containers.items():
                each = {}
                each.setdefault(host_ip, host_cons_mem_load)
                error_record.append(each)
                for container, mem_load_info in host_cons_mem_load.items():
                    failed_count += 1
        
        except:
            error_msg = str(traceback.format_exc())
            logging.error(error_msg)
            error_record.append(error_msg)
            
        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        super(CheckContainersMemLoad, self).write_status(0, 0, failed_count, 
                                                         alarm_level, error_record,
                                                         monitor_type, monitor_key) 

    def __get_host_overload_containers(self, containers_mem_load):
        ret = {}
        if isinstance(containers_mem_load, dict):
            for host_ip, host_cons_mem_load in containers_mem_load.items():
                overload_containers = {}
                for container, mem_load_info in host_cons_mem_load.items():
                    mem_load_rate = mem_load_info.get('mem_load_rate')
                    memsw_load_rate = mem_load_info.get('memsw_load_rate')
                    if mem_load_rate > 0.75 or memsw_load_rate > 0.75:
                        logging.info('mem_load_rate or memsw_load_rate bigger than 0.75: %s' % str(mem_load_rate) )
                        overload_containers.setdefault(container, mem_load_info)
                ret.setdefault(host_ip, overload_containers)
        else:
            ret.setdefault('code error', str(containers_mem_load) )
        return ret

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious
