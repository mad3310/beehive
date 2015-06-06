'''
Created on 2015-2-8

@author: asus
'''
import logging

from zk.zkOpers import Common_ZkOpers
from utils.exceptions import CommonException
from utils import nc_ip_port_available
from utils.threadUtil import doInThread


class PortOpers(object):
    '''
    classdocs
    '''
    
    def retrieve_port_resource(self, host_ip_list, every_host_port_count=1):

        port_dict = {}
        zkOper = Common_ZkOpers()
        try:
            isLock,lock = zkOper.lock_assign_port()
            if isLock:
                for host_ip in host_ip_list:
                    retrieve_port_list = zkOper.retrieve_port(host_ip, every_host_port_count)
                    port_dict.setdefault(host_ip, retrieve_port_list)
        finally:
            if isLock:
                zkOper.unLock_assign_port(lock)
            
        return port_dict

    def write_into_portPool(self, args):
        doInThread(self._write_into_portPool, args)

    def _write_into_portPool(self, args):
        host_ip = args.get('hostIp')
        port_count = int(args.get('portCount'))
        start_port = int(args.get('startPort'))

        choosed_ports = self.__get_needed_ports(host_ip, start_port, port_count)
        
        zkOper = Common_ZkOpers()

        for port in choosed_ports:
            zkOper.write_port_into_portPool(host_ip, str(port) )
        
    def get_port_num(self, host_ip):
        zkOper = Common_ZkOpers()
        port_list = zkOper.get_ports_from_portPool(host_ip)
        return len(port_list)

    def __get_needed_ports(self, host_ip, start_port, port_count):
        port_list = []
        while True:
            start_port += 1
            if start_port > 65535:
                raise CommonException('port are not enough, maybe start port are too small')
            if not nc_ip_port_available(host_ip, start_port):
                port_list.append(start_port)
            if len(port_list) >= port_count:
                break
        return port_list
        
    def get_illegal_ports(self, host_ip):
        
        illegal_ports = []
        
        zkOper = Common_ZkOpers()
        port_list = zkOper.get_ports_from_portPool(host_ip)
        logging.info('port in host: %s, in ports pool:%s ' % (host_ip, str(port_list) ))
        for port in port_list:
            ret = self.__port_legal(host_ip, port)
            if not ret:
                illegal_ports.append(port)
        return illegal_ports
                
    def __port_legal(self, ip, port):
        ret = nc_ip_port_available(ip, port)
        if ret:
            #logging.info('port: %s  is used :%s' % (port, str(ret)))
            return False
        else:
            return True