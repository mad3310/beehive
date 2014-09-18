#-*- coding: utf-8 -*-

from abstractContainerOpers import Abstract_Container_Opers

import pexpect
import commands

class MclusterManager(Abstract_Container_Opers):
        
    def destory(self):
        pass
    
    def create(self):
        pass

    def start(self, containerName = None):
        if containerName is None:
            return False
        containerID = commands.getoutput("docker ps |grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        child.sendline("service mcluster-manager restart")
        child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        child.close()

    def get_stat(self, containerName = None):
        stat = True
        containerID = commands.getoutput("docker ps|grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        child.sendline("curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'")
        index = child.expect(["successful", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        if index != 0:
            stat = False
        child.close(force=True)
        return stat
            
    def mcluster_manager_status(self, containerName = None):
        if containerName is None:
            return False
        if self.get_stat(containerName):
            return True
        self.start(containerName)
        return False
