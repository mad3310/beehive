#-*- coding: utf-8 -*-

import pexpect
import time

from componentProxy.baseComponentOpers import BaseComponentManager


class MclusterManager(BaseComponentManager):

    def __init__(self):
        self.timeout = 5

    def manager_status(self, container_name = None):
        if container_name is None:
            return False
        
        return self.__check(container_name)

    def __check(self, container_name = None):
        stat = True
        child = pexpect.spawn(r"docker attach %s" % container_name)
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("service %s restart" % self.component_manager)
            child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)

            time.sleep(1)
            child.sendline("service cbase status")
            index = child.expect(["running", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
        finally:
            child.close()
        
        return stat