'''
Created on Sep 8, 2014

@author: root
'''
import kazoo
import logging
import traceback

from tornado.web import asynchronous
from handlers.base import APIHandler
from common.tornado_basic_auth import require_basic_auth
from common.utils.exceptions import HTTPAPIError
from common.containerClusterOpers import ContainerCluster_Opers 
from common.ipOpers import IpOpers
from common.helper import *
from common.mclusterOper import MclusterManager

@require_basic_auth
class ContainerClusterHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # create container cluster
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=10.200.91.153&dataNodeName=docker_cluster_node_1" "http://localhost:8888/containerCluster"
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        try:
            res_reason = self.check_resource()
            if res_reason:
                raise HTTPAPIError(status_code=579, error_detail=res_reason)
            
            self.containerClusterOpers.create(args)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        dict = {} 
        dict.setdefault("message", "due to create container cluster need a little more times, please wait to finished and email to you, when cluster have started!")
        self.finish(dict)
    
    def check_resource(self):
        ip_list = self.zkOper.get_ips_from_ipPool()
        if len(ip_list) < 4:
            return 'ips are not enough!'

        
@require_basic_auth
class CheckContainerStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    @asynchronous
    def get(self, containerClusterName):        
        try:
            check_result =  self.containerClusterOpers.check(containerClusterName)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        
        self.finish(check_result)


@require_basic_auth
class AddIpsIntoIpPoolHandler(APIHandler):

    ip_opers = IpOpers()
    
    #curl --user root:root -d"ipSegment=10.200.85.xxx&&ipCount=50" http://localhost:8888/containerCluster/ips
    @asynchronous
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


class StartMclusterManagerHandler(APIHandler):

    mcluster_manager = MclusterManager()
    
    @asynchronous
    def get(self, container_name):
        ret = self.mcluster_manager.mcluster_manager_status(container_name)
        
        dict = {}
        dict.setdefault("message", ret)
        logging.info('handles status :  %s' % str(dict))
        self.finish(dict)


@require_basic_auth
class ClusterConfigHandler(APIHandler):
    
    containerClusterOpers = ContainerCluster_Opers()
    
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        try:
           self.containerClusterOpers.config(args)
        except:
            logging.error(str(traceback.format_exc()))
            raise HTTPAPIError(status_code=500, error_detail="write config infomation exception!",\
                                response =  "check if the zookeeper ensure the path!")
    
        dict = {}
        dict.setdefault("message", "write config infomation successfully!")
        self.finish(dict)
    

# @require_basic_auth
# class RemoveContainerClusterHandler(APIHandler):
#      
#     containerClusterOpers = ContainerCluster_Opers()
#      
#     @asynchronous
#     def post(self):
#         args = self.get_all_arguments()
#         try:
#             self.containerClusterOpers.destory(args)
#         except:
#             logging.error(str(traceback.format_exc()))
#             raise HTTPAPIError(status_code=417, error_detail="containerCluster removed failed!",\
#                                 response =  "check if the containerCluster removed!")
#      
#         dict = {}
#         dict.setdefault("message", "remove container has been done but need some time, please wait a little and check the result!")
#         self.finish(dict)