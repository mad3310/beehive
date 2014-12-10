#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

import logging

from base import APIHandler


# retrieve the status value of all monitor type 
# eg. curl "http://localhost:8888/mcluster/status"          
class ContainerStatus(APIHandler):
    def get(self):
        
        monitor_types = self.zkOper.retrieve_monitor_type()
        stat_dict = {}
        for monitor_type in monitor_types:
            monitor_status_list = self.zkOper.retrieve_monitor_status_list(monitor_type)
            monitor_status_list_count = len(monitor_status_list)
        
            monitor_type_sub_dict = {}
            for monitor_status_key in monitor_status_list:
                monitor_status_value = self.zkOper.retrieve_monitor_status_value(monitor_type, monitor_status_key)
                monitor_type_sub_dict.setdefault(monitor_status_key, monitor_status_value)
                
            stat_dict.setdefault(monitor_type, monitor_type_sub_dict)

        self.finish(stat_dict)