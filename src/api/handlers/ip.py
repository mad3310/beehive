#-*- coding: utf-8 -*-
from handlers.base import APIHandler
from utils.exceptions import HTTPAPIError
from resource_letv.ipOpers import IpOpers
from zk.zkOpers import ZkOpers
from tornado_letv.tornado_basic_auth import require_basic_auth


@require_basic_auth
class IPHandler(APIHandler):
    
    ip_opers = IpOpers()
    zkOper = ZkOpers()
    
    #curl --user root:root -d"ipSegment=10.200.85.xxx&&ipCount=50" http://localhost:8888/admin/ips
    def post(self):
        args = self.get_all_arguments()
        try:
            self.ip_opers.write_into_ipPool(args)
        except:
            raise HTTPAPIError(status_code=500, error_detail="lock by other thread on assign ip processing",\
                                response =  "check if the zookeeper ensure the path!")
        
        return_message = {}
        return_message.setdefault("message", "write ip to ip pools successfully!")
        self.finish(return_message)
        
    def get(self):
        return_message = {}
        ips = self.zkOper.get_ips_from_ipPool()
        return_message.setdefault('ips', ips)
        self.finish(return_message)


@require_basic_auth
class FetchIpHandler(APIHandler):
    
    ip_opers = IpOpers()
    
    #curl --user root:root -d"num=1" http://localhost:8888/resource/ip
    def post(self):
        num = self.get_argument('num', 1)
        ip_list = self.ip_opers.retrieve_ip_resource(int(num))
        
        return_message = {}
        return_message.setdefault("ip", ip_list)
        self.finish(return_message)
