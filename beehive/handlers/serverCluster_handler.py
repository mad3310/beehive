#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import uuid
import json
import logging
import urllib

from tornado.options import options
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.web import asynchronous
from tornado.gen import engine, Task
from tornadoForBeehive.tornado_basic_auth import require_basic_auth

from utils.configFileOpers import ConfigFileOpers
from utils import _retrieve_userName_passwd, async_http_post
from utils.exceptions import HTTPAPIError
from base import APIHandler
from zk.zkOpers import Requests_ZkOpers
from serverCluster.serverClusterOpers import ServerCluster_Opers


@require_basic_auth
class ServerClusterHandler(APIHandler):
    '''
    classdocs
    '''
    confOpers = ConfigFileOpers()

    # create server cluster
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=192.168.84.132&dataNodeName=docker_cluster_node_1" "http://localhost:8888/serverCluster"
    def post(self):
        requestParam = self.get_all_arguments()
        
        zkOper = Requests_ZkOpers()
        
        existCluster = zkOper.existCluster()
        if existCluster:
            clusterUUID = zkOper.getClusterUUID()
        else:
            clusterUUID = str(uuid.uuid1())
            requestParam.setdefault("clusterUUID", clusterUUID)
        
        if requestParam != {}:
            self.confOpers.setValue(options.server_cluster_property, requestParam)
            self.confOpers.setValue(options.data_node_property, requestParam)
          
        clusterProps = self.confOpers.getValue(options.server_cluster_property)
        dataNodeProprs = self.confOpers.getValue(options.data_node_property)
        zkOper.writeClusterInfo(clusterUUID, clusterProps)
        zkOper.writeDataNodeInfo(clusterUUID, dataNodeProprs)

        return_message = {}
        return_message.setdefault("message", "creating server cluster successful!")
        self.finish(return_message)
        
    def get(self):
        zkOper = Requests_ZkOpers()

        clusterUUID = zkOper.getClusterUUID()
        data, _ = zkOper.retrieveClusterProp(clusterUUID)
        self.confOpers.setValue(options.server_cluster_property, eval(data))
        
        result = {}
        result.setdefault("message", "sync server cluster info to local successful!")
        self.finish(result)

class SyncServerClusterHandler(APIHandler):
    """
    update serverCluster 
    """
    
    serverCluster_opers = ServerCluster_Opers()
    
    # eg. curl --user root:root -X GET http://localhost:8888/serverCluster/update
    def get(self):
        
        self.serverCluster_opers.sync()

        return_message = {}
        return_message.setdefault("message", "serverCluster update successful")
        self.finish(return_message)
