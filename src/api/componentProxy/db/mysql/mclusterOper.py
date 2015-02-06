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
    
    def validate_manager_status(self, create_container_node_ip_list, create_container_arg_list, num):
        container_name_list = []
        check_container_node_ip_list = []
        for index, create_container_arg in enumerate(create_container_arg_list):
            if create_container_arg.get('container_type') == 'mclusternode':
                container_name_list.append(create_container_arg.get('container_name'))
                check_container_node_ip_list.append(create_container_node_ip_list[index])
        logging.info('wait 5 seconds...')
        time.sleep(5)
        while num:
            stat = True
            succ = {}
            logging.info('check_container_node_ip_list :%s' % str(check_container_node_ip_list) )
            for index,host_ip in enumerate(check_container_node_ip_list):
                container_name = container_name_list[index]
                ret = self.__get(container_name, host_ip)
                logging.info('check container %s,  result : %s' % (container_name, str(ret)))
                if ret:
                    succ.setdefault(host_ip, container_name)
                else:
                    stat = False
            logging.info('stat: %s' % str(stat))
            if stat:
                logging.info('successful!!!')
                return True
            
            for hostip, containername in succ.items():
                container_name_list.remove(containername)
                check_container_node_ip_list.remove(hostip)
            num -= 1
    
    def __get(self, containerName, container_node):
        ret = False
        url_post = "/inner/MclusterManager/status/%s" % containerName
        requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
        logging.debug('requesturi: %s' % requesturi)
        fetch_ret = http_get(requesturi)
        logging.info('fetch_ret:%s' % str(fetch_ret))
        ret = fetch_ret.get('response').get('message')
        logging.debug('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
        logging.debug('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
        return ret
