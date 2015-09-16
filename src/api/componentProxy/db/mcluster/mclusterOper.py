#-*- coding: utf-8 -*-

import pexpect
import time
from componentProxy.baseComponentOpers import BaseComponentManager


class MclusterManager(BaseComponentManager):

    def __init__(self):
        self.timeout = 5

    def __start(self, container_name = None):
        child = pexpect.spawn(r"docker attach %s" % container_name)
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("""[[ $(grep -c "GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' IDENTIFIED BY 'Mcluster' WITH GRANT OPTION;" /usr/share/mysql/mcluster-bootstrap) -eq 0 ]] && sed -i "/DROP DATABASE test/i\GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' IDENTIFIED BY 'Mcluster' WITH GRANT OPTION;" /usr/share/mysql/mcluster-bootstrap""")
            child.expect(["bash",pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("""[[ $(grep -c "GRANT RELOAD, LOCK TABLES, REPLICATION CLIENT, CREATE TABLESPACE, SUPER ON *.* TO 'backup'@'%' IDENTIFIED BY 'backup';" /usr/share/mysql/mcluster-bootstrap) -eq 0 ]] && sed -i "/DROP DATABASE test/i\GRANT RELOAD, LOCK TABLES, REPLICATION CLIENT, CREATE TABLESPACE, SUPER ON *.* TO 'backup'@'%' IDENTIFIED BY 'backup';" /usr/share/mysql/mcluster-bootstrap""")
            child.expect(["bash",pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("service mcluster-manager restart")
            child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        finally:
            child.close()

    def __get_stat(self, container_name = None):
        stat = True
        child = pexpect.spawn(r"docker attach %s" % container_name)
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("curl 'http://127.0.0.1:8888/mcluster/health'") 
            index = child.expect(["ok", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
        finally:
            child.close()
        
        return stat

    def manager_status(self, container_name = None):
        if container_name is None:
            return False
        
        self.__start(container_name)
        time.sleep(1)
        return self.__get_stat(container_name)
