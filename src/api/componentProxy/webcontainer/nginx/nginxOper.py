#-*- coding: utf-8 -*-

import pexpect
import time


class NginxManager(object):

    def __init__(self):
        self.timeout = 5

    def __start(self, containerName = None):
        child = pexpect.spawn(r"docker attach %s" % containerName)
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("service nginx-manager restart")
            child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        finally:
            child.close()

    def __get_stat(self, containerName = None):
        stat = True
        child = pexpect.spawn(r"docker attach %s" % containerName)
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'")
            index = child.expect(["successful", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
        finally:
            child.close()
        return stat

    def manager_status(self, containerName = None):
        if containerName is None:
            return False
        self.__start(containerName)
        time.sleep(1)
        return self.__get_stat(containerName)
