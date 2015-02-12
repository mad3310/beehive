#-*- coding: utf-8 -*-

import pexpect
import commands
import time
import logging

class MclusterManager(object):
    
    def __init__(self):
        self.timeout = 5
        
    def __start(self, containerName = None):
        containerID = commands.getoutput("docker ps |grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        
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
        
    def __get_stat(self, containerName = None):
        stat = True
        containerID = commands.getoutput("docker ps|grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        
        try:
            child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            child.sendline("curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'")
            index = child.expect(["successful", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
            if index != 0:
                stat = False
        finally:
            child.close()
        
        return stat

    def mcluster_manager_status(self, containerName = None):
        if containerName is None:
            return False
        self.__start(containerName)
        time.sleep(1)
        if self.__get_stat(containerName):
            return True
        return False


