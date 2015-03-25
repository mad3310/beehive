#-*- coding: utf-8 -*-

import pexpect
import time


class BaseComponentManager(object):

    def __init__(self, component_manager):
        self.timeout = 5
        self.component_manager = component_manager

    def manager_status(self, container_name = None):
        if container_name is None:
            return False
        self.__start(container_name)
        time.sleep(1)
        return self.__get_stat(container_name)

    def __start(self, container_name = None):
        child = pexpect.spawn(r"docker attach %s" % container_name)
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("service %s restart" % self.component_manager)
            child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        finally:
            child.close()

    def __get_stat(self, container_name = None):
        stat = True
        child = pexpect.spawn(r"docker attach %s" % container_name)
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'")
            index = child.expect(["successful", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
        finally:
            child.close()
        return stat