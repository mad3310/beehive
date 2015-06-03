#!/usr/bin/env python 2.6.6

import logging
import datetime

from tornado.options import options
from abc import abstractmethod
from zk.zkOpers import Scheduler_ZkOpers
from resource_letv.ipOpers import IpOpers
from resource_letv.portOpers import PortOpers
from server.serverOpers import Server_Opers

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class CheckStatusBase(object):
    
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
        
        zkOper = Scheduler_ZkOpers()
        zkOper.write_monitor_status(monitor_type, monitor_key, result_dict)


class CheckResIpNum(CheckStatusBase):
    ip_opers = IpOpers()

    def check(self):

        monitor_type, monitor_key, error_record = 'res', 'ip_num', ''
        success_count = self.ip_opers.get_ip_num()
        if success_count < 20:
            error_record = 'the number of ips in ip Pool is %s, please add ips!' % success_count
        alarm_level = self.retrieve_alarm_level(0, success_count, 0)
        super(CheckResIpNum, self).write_status(0, success_count, 0, \
                                                alarm_level, error_record, 
                                                monitor_type, monitor_key)
        

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if 20 < success_count:
            return options.alarm_nothing
        elif 15 < success_count <= 20:
            return options.alarm_general
        else:
            return options.alarm_serious


class CheckServerPortNum(CheckStatusBase):
    port_opers = PortOpers()

    def check(self):

        monitor_type, monitor_key, error_record = 'res', 'port_num', ''
        
        zk_opers = Scheduler_ZkOpers()
        host_ip_list = zk_opers.retrieve_data_node_list()
        for host_ip in host_ip_list:
            success_count = self.port_opers.get_port_num(host_ip)
            if success_count < 30:
                error_record += 'the number of port in port Pool is %s on server :%s, please add ports!\n' % (success_count, host_ip)
        
        alarm_level = self.retrieve_alarm_level(0, success_count, 0)
        super(CheckServerPortNum, self).write_status(0, 0, 0, \
                                                     alarm_level, error_record, 
                                                     monitor_type, monitor_key)
    
    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if 30 < success_count:
            return options.alarm_nothing
        elif 20 < success_count <= 30:
            return options.alarm_general
        else:
            return options.alarm_serious


class CheckResIpLegality(CheckStatusBase):
    
    ip_opers = IpOpers()
    
    def check(self):
        monitor_type, monitor_key = 'res', 'ip_usable'

        logging.info('do get_illegal_ips')
        error_record = self.ip_opers.get_illegal_ips(20)
        failed_count = len(error_record)
        logging.info('check ip res result, such ips can be pingable : %s' % failed_count)
        
        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        super(CheckResIpLegality, self).write_status(0, 0, \
                                                    failed_count, \
                                                    alarm_level, error_record, monitor_type, \
                                                    monitor_key)
        
    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious


class CheckContainersKeyValue(CheckStatusBase):
    
    server_opers = Server_Opers()
    
    def __init__(self, monitor_key, value):
        super(CheckContainersKeyValue, self).__init__()
        self.monitor_key = monitor_key
        self.value = value
    
    def check(self):
        monitor_type,  error_record = 'container', []
        failed_count = 0
        
        logging.info('do check under_oom')
        zk_opers = Scheduler_ZkOpers()

        server_list = zk_opers.retrieve_servers_white_list()
        for server in server_list:
            under_oom_info = zk_opers.retrieveDataNodeContainersResource(server, self.monitor_key)
            '''
                if new server join server cluster,there
            '''
            if not under_oom_info:
                return
            container_under_oom_dict = under_oom_info.get(self.monitor_key)
            for container, under_oom_value in container_under_oom_dict.items():
                if under_oom_value != self.value:
                    error_record.append(container)
                    failed_count = len(error_record)

        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        self.write_status(0, 0, failed_count, alarm_level, error_record, monitor_type, self.monitor_key)      

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious


class CheckContainersUnderOom(CheckContainersKeyValue):
    
    def __init__(self):
        super(CheckContainersUnderOom, self).__init__('under_oom', 0)


class CheckContainersOomKillDisable(CheckContainersKeyValue):
    
    def __init__(self):
        super(CheckContainersOomKillDisable, self).__init__('oom_kill_disable', 1)