'''
Created on Sep 8, 2014

@author: root
'''
import kazoo

from tornado.web import asynchronous
from handlers.base import APIHandler
from common.tornado_basic_auth import require_basic_auth
from common.utils.exceptions import HTTPAPIError
from common.containerClusterOpers import ContainerCluster_Opers 
from common.ipOpers import IpOpers
from common.helper import *
from common.mclusterOper import MclusterManager
from MySQLdb.constants.ER import LOGGING_PROHIBIT_CHANGING_OF

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
            self.containerClusterOpers.create(args)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        
        dict = {}
        dict.setdefault("message", "due to create container cluster need a large of times, please wait to finished and email to you, when cluster have started!")
        self.finish(dict)
        
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
            raise HTTPAPIError(status_code=579, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        
        self.finish(check_result)

@require_basic_auth
class AddIpsIntoIpPoolHandler(APIHandler):

    ip_opers = IpOpers()
    
    # write ips into ippool
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=10.200.91.153&dataNodeName=docker_cluster_node_1" "http://localhost:8888/containerCluster"
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        try:
            self.ip_opers.write_into_ipPool(args)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        
        dict = {}
        dict.setdefault("message", "write ip to ip pools successful!")
        self.finish(dict)

class StartMclusterManagerHandler(APIHandler):

    mcluster_manager = MclusterManager()
    
    # write ips into ippool
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=10.200.91.153&dataNodeName=docker_cluster_node_1" "http://localhost:8888/containerCluster"
    @asynchronous
    def get(self, container_name):
        ret = self.mcluster_manager.mcluster_manager_status(container_name)
        
        dict = {}
        dict.setdefault("message", ret)
        self.finish(dict)