#!/usr/bin/env python 2.6.6

import logging
import datetime
import traceback

from tornado.options import options
from abc import abstractmethod
from zk.zkOpers import ZkOpers
from resource_letv.ipOpers import IpOpers
from server.serverOpers import Server_Opers
from utils import _retrieve_userName_passwd, getHostIp, http_get

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
        
        zkOper = ZkOpers()
        try:
            zkOper.write_monitor_status(monitor_type, monitor_key, result_dict)
        finally:
            zkOper.close()
        

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


class CheckResIpLegality(CheckStatusBase):
    
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
            '''
            @todo: if occurs exception, the code will be continue run?
            '''
            error_msg = str(traceback.format_exc())
            logging.error(error_msg)
            failed_count = 1
            error_record.append(error_msg)
            
            
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


class CheckContainersUnderOom(CheckStatusBase):
    
    server_opers = Server_Opers()
    
    def check(self):
        monitor_type, monitor_key, error_record = 'container', 'under_oom', []
        failed_count = 0

        logging.info('do check under_oom')
        zk_opers = ZkOpers()
        try:
            server_list = zk_opers.retrieve_servers_white_list()
            for server in server_list:
                under_oom_info = zk_opers.retrieveDataNodeContainersResource(server, 'under_oom')
                for container, under_oom_value_dict in under_oom_info.items():
                    if under_oom_value_dict.get('under_oom') != 0:
                        error_record.append(container)
                        failed_count = len(error_record)
                        
        finally:
            zk_opers.close()
        
        alarm_level = self.retrieve_alarm_level(0, 0, failed_count)
        super(CheckContainersUnderOom, self).write_status(0, 0, failed_count, 
                                                          alarm_level, error_record,
                                                          monitor_type, monitor_key)      

    def retrieve_alarm_level(self, total_count, success_count, failed_count):
        if failed_count == 0:
            return options.alarm_nothing
        else:
            return options.alarm_serious
