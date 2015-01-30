#-*- coding: utf-8 -*-
from base import APIHandler
from common.ipOpers import IpOpers
# ip management
# eg. ？？？
@require_basic_auth
class IPHandler(APIHandler):
    
    ip_opers = IpOpers()
    
    #curl --user root:root -d"ipSegment=10.200.85.xxx&&ipCount=50" http://localhost:8888/containerCluster/ips
    def post(self):
        args = self.get_all_arguments()
        try:
            self.ip_opers.write_into_ipPool(args)
        except:
            raise HTTPAPIError(status_code=500, error_detail="lock by other thread on assign ip processing",\
                                response =  "check if the zookeeper ensure the path!")
        
        dict = {}
        dict.setdefault("message", "write ip to ip pools successfully!")
        self.finish(dict)        
        
    def get(self):
        result, ips = {}, []
        try:
            ips = self.ip_opers.get_ips_from_ipPool()
        except:
            raise HTTPAPIError(status_code=500, error_detail="code error!",\
                            notification = "direct", \
                            log_message= "code error!",\
                            response =  "code error!")
        
        result.setdefault('ips', ips)
        self.finish(result)
