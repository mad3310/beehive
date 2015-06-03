#-*- coding: utf-8 -*-
from handlers.base import APIHandler
from resource_letv.ipOpers import IpOpers
from zk.zkOpers import Requests_ZkOpers
from tornado_letv.tornado_basic_auth import require_basic_auth


@require_basic_auth
class IPHandler(APIHandler):
    
    ip_opers = IpOpers()
    
    #curl --user root:root -d"ipSegment=10.200.85.xxx&&ipCount=50" http://localhost:8888/admin/ips
    def post(self):
        args = self.get_all_arguments()
        self.ip_opers.write_into_ipPool(args)
        
        result = {}
        result.setdefault("message", "write ip to ip pools successfully!")
        self.finish(result)
        
    def get(self):
        zkOper = Requests_ZkOpers()
        ips = zkOper.get_ips_from_ipPool()
        result = {}
        result.setdefault('ips', ips)
        self.finish(result)


@require_basic_auth
class FetchIpHandler(APIHandler):
    
    ip_opers = IpOpers()
    
    #curl --user root:root -d"num=1" http://localhost:8888/resource/ip
    def post(self):
        num = self.get_argument('num', 1)
        ip_list = self.ip_opers.retrieve_ip_resource(int(num))
        
        result = {}
        result.setdefault("ip", ip_list)
        self.finish(result)
