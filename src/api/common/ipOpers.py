#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 17, 2014

@author: root
'''

import os
from abstractContainerOpers import Abstract_Container_Opers

class IpOpers(Abstract_Container_Opers):
    '''
    classdocs
    '''
    
    def write_into_ipPool(self, args_dict):
        ip_segment = args_dict.get('ipSegment')
        ip_count = int(args_dict.get('ipCount'))
        ip_list = self.zkOper.get_ips_from_ipPool()
        all_ips = self._get_all_ips(ip_segment)
        ips = list( set(all_ips) - set(ip_list) )
        if len(ips) <= ip_count:
            ip_count = len(ips)
        for i in range(ip_count):
            ip = ips[i]
            self.zkOper.write_ip_into_ipPool(ip)
    
    def _get_all_ips(self, ip_segment):
        all_ips = []
        ip_items = ip_segment.split('.')
        for i in range(2, 254):
            ip_items[-1] = str(i)
            ip = '.'.join(ip_items)
            if not self._ping_ip_usable(ip):
                continue
            all_ips.append(ip)
        return all_ips
    
    def _ping_ip_usable(self, ip):
        cmd = 'ping -w 1 %s' % str(ip)
        ping_ret = os.system(cmd)
        if ping_ret != 0:
            return True

if __name__ == '__main__':
    ipops = IpOpers()
    print ipops._ping_ip_usable('10.200.85.28')
#    print os.system('docker ps')