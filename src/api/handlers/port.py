#-*- coding: utf-8 -*-
import logging

from handlers.base import APIHandler
from resource_letv.portOpers import PortOpers
from zk.zkOpers import ZkOpers
from tornado_letv.tornado_basic_auth import require_basic_auth

# ip management
'''
@todo: every interface need to add comment for the curl usage
'''

@require_basic_auth
class PortHandler(APIHandler):
    
    port_opers = PortOpers()
    zkOper = ZkOpers()
    
    #curl --user root:root -d"startPort=38888&portCount=100&hostIp=10.154.156.150" http://localhost:8888/admin/ports
    def post(self):
        args = self.get_all_arguments()
        self.port_opers.write_into_portPool(args)
        return_message = {}
        return_message.setdefault("message", "write port to ip pools successfully!")
        self.finish(return_message)

    #curl --user root:root -X GET http://localhost:8888/admin/ports?hostIp=10.154.156.150
    def get(self):
        args = self.get_all_arguments()
        host_ip = args.get('hostIp')
        logging.info('get server %s ports' % host_ip)
        return_message = {}
        ports = self.zkOper.get_ports_from_portPool(host_ip)
        return_message.setdefault('ports', ports)
        self.finish(return_message)
