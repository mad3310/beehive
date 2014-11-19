#-*- coding: utf-8 -*-

from abstractContainerOpers import Abstract_Container_Opers

import pexpect
import commands
import os
import time
import logging

class MclusterManager(Abstract_Container_Opers):
    
    def __init__(self):
        self.timeout = 5
        
    def destory(self):
        pass
    
    def create(self):
        pass

    def start(self, containerName = None):
        containerID = commands.getoutput("docker ps |grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.sendline("""[[ $(grep -c "GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' IDENTIFIED BY 'Mcluster' WITH GRANT OPTION;" /usr/share/mysql/mcluster-bootstrap) -eq 0 ]] && sed -i "/DROP DATABASE test/i\GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' IDENTIFIED BY 'Mcluster' WITH GRANT OPTION;" /usr/share/mysql/mcluster-bootstrap""")
        child.expect(["bash",pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.sendline("service mcluster-manager restart")
        child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.close()

    def get_stat(self, containerName = None):
        stat = True
        containerID = commands.getoutput("docker ps|grep -w %s|awk '{print $1}'" % (containerName))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.sendline("curl -d 'zkAddress=127.0.0.1' 'http://127.0.0.1:8888/admin/conf'")
        index = child.expect(["successful", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        if index != 0:
            stat = False
        child.close()
        return stat

    def update_mcluster_manager(self, containerName = None):
        containerID = commands.getoutput("docker ps |grep -w %s|awk '{print $1}'" % (containerName))
        fullID = commands.getoutput("docker inspect %s|awk '/Id/{print $2}'" % (containerID))
        fullID = fullID.replace('"', '').replace(',', '')
        target_file = "/srv/docker/devicemapper/mnt/%s/rootfs/tmp/mcluster-manager-0.0.1-21.el6.noarch.rpm"  % (fullID)
        if not os.path.exists(target_file):
            os.system("cp /tmp/mcluster-manager-0.0.1-21.el6.noarch.rpm %s" % (target_file))
        child = pexpect.spawn(r"docker attach %s" % (containerID))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        #child.sendline("rpm -qa mcluster-manager")
        #child.expect(["0.0.1.*.el6", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        #version = child.after.replace('.el6','')
        #if version:
            #logging.info('version: %s' % str(version) )
            #ver, sub = version.split("-")
            #if ver == '0.0.1' and int(sub) < 37:
        child.sendline("service mcluster-manager stop")
        child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.sendline("rpm -U /tmp/mcluster-manager-0.0.1-21.el6.noarch.rpm")
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.sendline("service mcluster-manager start")
        child.expect(["OK", pexpect.EOF, pexpect.TIMEOUT], timeout=self.timeout)
        child.close(force=True)
            
    def mcluster_manager_status(self, containerName = None):
        if containerName is None:
            return False
        #self.update_mcluster_manager(containerName)
        self.start(containerName)
        time.sleep(1)
        if self.get_stat(containerName):
            return True
        return False
