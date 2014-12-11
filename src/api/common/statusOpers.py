#!/usr/bin/env python 2.6.6

import logging
import datetime
import traceback
import re

from common.zkOpers import ZkOpers
from tornado.options import options
from abc import abstractmethod
from ipOpers import IpOpers


TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class CheckStatusBase(object):
    
    zkOper = ZkOpers('127.0.0.1',2181)
    
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
    
   
        result_dict = {}
        format_str = "total=%s, success count=%s, failed count=%s"
        format_values = (total_count, success_count, failed_count)
        message = format_str % format_values
        dt = datetime.datetime.now()
        result_dict.setdefault("message", message)
        result_dict.setdefault("alarm", alarm_level)
        result_dict.setdefault("error_record", error_record)
        result_dict.setdefault("ctime", dt.strftime(TIME_FORMAT))
        
        self.zkOper.write_monitor_status(monitor_type, monitor_key, result_dict)

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
        monitor_type, monitor_key, error_record = 'res', 'ip_usable', ''
        failed_count = 0
        try:
            logging.info('do get_illegal_ips')
            unusable_ip_list = self.ip_opers.get_illegal_ips(20)
            failed_count = len(unusable_ip_list)
            if failed_count:
                for ip in unusable_ip_list:
                    error_record += 'ip: %s,' % str(ip)
            logging.info('check ip res resutl failed_count : %s' % failed_count)
        except:
            logging.error( str(traceback.format_exc()) )
            
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
