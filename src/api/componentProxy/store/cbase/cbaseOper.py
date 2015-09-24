#-*- coding: utf-8 -*-

import os
from tornado.options import options
from status.status_enum import Flag

from componentProxy.baseComponentOpers import BaseComponentManager


class CbaseManager(BaseComponentManager):

    def __init__(self):
        self.timeout = 5

    def manager_status(self, container_name):
        command = "docker ps | grep %s | awk '{print $1}'" % container_name 
        ret = os.popen(command)
        container_id = ret.read().strip()
        return self.__check(container_id)

    def __check(self, container_id = None):
        
        stat = True
        nsenter = options.nsenter % container_id
        
        cbase_status_cmd = nsenter + ' service cbase status'
        ret = os.popen(cbase_status_cmd)
        status = ret.read()
        if not Flag.running in status:
            stat = False
            cbase_restart_cmd = nsenter + ' service cbase restart'
            os.system(cbase_restart_cmd)
        
        return stat