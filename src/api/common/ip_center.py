#!/usr/bin/env python
from invokeCommand import InvokeCommand
import logging
from tornado.options import options
import socket
import docker
#import os,sys,inspect

class Ip_Center(object):
    """
    classdocs
    """
    def get_host_ip(self):
        host_ip = socket.gethostbyname(socket.gethostname())
        return host_ip
    
    def get_containers_name(self):
        invokeCmd = InvokeCommand()
        ret_sub_p = invokeCmd._runSysCmd('docker ps') 
        contents =  ret_sub_p[0].split()
        names = []
        list = []
        length = len(contents)
        cycle = 10
        start_index = 8
        if start_index < length:
            logging.info("This host have no container")
        while start_index < length:
            list.append(contents[start_index])
            start_index += cycle
        logging.info("containers' names: " + str(list))
        return list

    def get_containers_ip(self):
        names = self.get_containers_name() 
        
        _invokeCmd = InvokeCommand()
        container_ip_list = []
        for name in names:
            #_shell = "docker inspect --format '{{ .NetworkSettings.IPAddress }}' "  + name  
            _shell = "docker inspect  "  + name  
            ret_sub_p = _invokeCmd._runSysCmd(_shell)
         
            print ret_sub_p
        #    container_ip_list.append(ret_sub_p[0].rstrip())

        #logging.info("containers' names: " + str(container_ip_list))
        #return container_ip_list
    def get_ips(self):
        ip_set = {}
        host_ip = self.get_host_ip()
        containers_ip = self.get_containers_ip()
        ip_set.setdefault("host_ip", host_ip)
        ip_set.setdefault("containers_ip", containers_ip)
        
        return ip_set 
if __name__ == '__main__':
    ip_center = Ip_Center()
    print "ip_center work"
    print "host ip address :" , ip_center.get_host_ip()
    print "ip set :", ip_center.get_ips()
