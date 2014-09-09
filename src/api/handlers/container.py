#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging

from base import APIHandler
from api.common.containerOpers import Container_Opers
from api.common.utils.exceptions import HTTPAPIError
from api.common.tornado_basic_auth import require_basic_auth

@require_basic_auth
class ContainerHandler(APIHandler):
    
    containerOpers = Container_Opers()
    """
    create container
    "code":000001 arg wrong
    000002: create container failed
    """
    
    def post(self):
        args = self.get_all_arguments()
        logging.debug('all_arguments: %s' % str(args))
        
        container_name = args.get('containerName', 'my_container')
        logging.debug('containerName: %s' % container_name)
        
        container_type = args.get('containerType', 'mclusternode')
        logging.debug('containerType: %s' % container_type)
        
        ip_address = args.get('containerIp', '127.0.0.1')
        logging.debug('containerIp: %s' % ip_address)
        
        error_resaon = None
        gateway = args.get('gw', None)
        if not gateway:
            logging.error('没有得到container的网关')
            error_resaon = 'no geteAddr in the arguments'
        netmark = args.get('netMark', None)
        if not netmark:
            logging.error('没有得到container的子网掩码')
            error_resaon = 'no netMark in the arguments'
        if error_resaon:
            self.finish( {"code":000001, "msg":error_resaon} )
            return
        
        zk_id = args.get('zkid')
        
        n1_ip = args.get('n1_ip')
        n1_hostname = args.get('n1_hostname')
        n2_ip = args.get('n2_ip')
        n2_hostname = args.get('n2_hostname')
        n3_ip = args.get('n3_ip')
        n3_hostname = args.get('n3_hostname')
        
        dict = {}
        dict.setdefault('containerName', container_name)
        dict.setdefault('containerType', container_type)
        dict.setdefault('HOSTNAME', container_name)
        dict.setdefault('IP', ip_address)
        dict.setdefault('GATEWAY', gateway)
        dict.setdefault('NETMASK', netmark)
        dict.setdefault('ZKID', zk_id)
        dict.setdefault('N1_IP', n1_ip)
        dict.setdefault('N2_IP', n2_ip)
        dict.setdefault('N3_IP', n3_ip)
        dict.setdefault('N1_HOSTNAME', n1_hostname)
        dict.setdefault('N2_HOSTNAME', n2_hostname)
        dict.setdefault('N3_HOSTNAME', n3_hostname)
        
        create_rst = self.containerOpers.create_container(dict)
        
        if create_rst:
            raise HTTPAPIError(status_code=417, error_detail="container created failed!",\
                                notification = "direct", \
                                log_message= "container created failed!",\
                                response =  "container created failed!")
        
        dict = {}
        dict.setdefault("message", "Success Create Container")
        
        self.finish(dict)