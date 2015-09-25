#-*- coding: utf-8 -*-

import os
import logging

from tornado.options import options
from status.status_enum import Flag

class BaseComponentManager(object):

    def __init__(self, component_manager, validate_cmd=None, validate_flag=None):
        self.component_manager = component_manager
        self.validate_cmd = validate_cmd
        self.validate_flag = validate_flag

    def manager_status(self, container_name):
        command = "docker ps | grep %s | awk '{print $1}'" % container_name 
        ret = os.popen(command)
        container_id = ret.read().strip()
        return self.__check(container_id)

    def __check(self, container_id):
        
        result = True
        
        nsenter = options.nsenter % container_id
        cmd = self.validate_cmd if self.validate_cmd else "curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'"
        curl_cmd = nsenter + cmd
        logging.info('curl check:%s' % curl_cmd)
        ret = os.popen(curl_cmd)
        status = ret.read()
        
        flag = self.validate_flag if self.validate_flag else Flag.successful
        
        if not flag in status:
            result = False
            component_restart_cmd = nsenter + 'service %s restart' % self.component_manager
            os.system(component_restart_cmd)
        
        return result