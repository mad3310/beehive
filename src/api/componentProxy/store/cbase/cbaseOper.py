#-*- coding: utf-8 -*-

import pexpect

from componentProxy.baseComponentOpers import BaseComponentManager


class CbaseManager(BaseComponentManager):

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
            child.sendline("service cbase status")
            index = child.expect(["running", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
                child.sendline("service cbase restart")
                child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        finally:
            child.close()
        
        return stat