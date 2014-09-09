'''
Created on Sep 8, 2014

@author: root
'''
import kazoo

from tornado.web import asynchronous
from api.handlers.base import APIHandler
from api.common.tornado_basic_auth import require_basic_auth
from api.common.utils.exceptions import HTTPAPIError
from api.common.containerClusterOpers import ContainerCluster_Opers

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