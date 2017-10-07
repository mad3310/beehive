#-*- coding: utf-8 -*-
import logging

from handlers.base import APIHandler
from resourceForBeehive.portOpers import PortOpers
from zk.zkOpers import Requests_ZkOpers
from tornado_letv.tornado_basic_auth import require_basic_auth


@require_basic_auth
class PortHandler(APIHandler):
    
    port_opers = PortOpers()
    
    #curl --user root:root -d"startPort=38888&portCount=100&hostIp=10.154.156.150" http://localhost:8888/admin/ports
    def post(self):
        args = self.get_all_arguments()
        self.port_opers.write_into_portPool(args)
        
        result = {}
        result.setdefault("message", "ports have already been added, please check!")
        self.finish(result)

    #curl --user root:root -X GET http://localhost:8888/admin/ports?hostIp=10.154.156.150
    def get(self):
        args = self.get_all_arguments()
        host_ip = args.get('hostIp')
        logging.info('get server %s ports' % host_ip)
        
        zkOper = Requests_ZkOpers()
        ports = zkOper.get_ports_from_portPool(host_ip)
        
        result = {}
        result.setdefault('ports', ports)
        self.finish(result)
