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
from tornado_letv.tornado_basic_auth import require_basic_auth

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


@require_basic_auth
class SwitchServersUnderoomHandler(APIHandler):
    
    # eg. curl --user root:root -d "switch=on&containerNameList=d-mcl-xiangge-n-2,d-mcl-xiangge-n-1" "http://localhost:8888/serverCluster/containers/under_oom"
    @asynchronous
    @engine
    def post(self):
        
        args = self.get_all_arguments()
        switch = args.get('switch')
        
        if not switch or (switch!='on' and switch!='off'):
            raise HTTPAPIError(status_code=417, error_detail="switch params wrong!",\
                                notification = "direct", \
                                log_message= "switch params wrong!",\
                                response =  "please check params!")
        
        containers = args.get('containerNameList')
        container_name_list = containers.split(',')
        if not (container_name_list and isinstance(container_name_list, list)):
            raise HTTPAPIError(status_code=417, error_detail="containerNameList params not given correct!",\
                                notification = "direct", \
                                log_message= "containerNameList params not given correct!",\
                                response =  "please check params!")
        
        zkOper = Requests_ZkOpers()
        server_list = zkOper.retrieve_servers_white_list()
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        
        result = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/server/containers/under_oom' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                response = async_http_post(async_client, requesturi, args, 40, 40, auth_username, auth_password) 
                body = json.loads( response.body.strip())
                ret =  body.get('response')
                result.update(ret)
        finally:
            async_client.close()
            
        except_cons = list(set(container_name_list) - set(result.keys()))
        for con in except_cons:
            result.setdefault(con, 'no such container or code exception')
        self.finish(result)


@require_basic_auth
class AddServersMemoryHandler(APIHandler):
    
    @asynchronous
    @engine
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        logging.info('get servers containers memory load method, containerNameList:%s' % str(containers) )
        container_name_list = containers.split(',')
        if not (container_name_list and isinstance(container_name_list, list)):
            raise HTTPAPIError(status_code=417, error_detail="containerNameList is illegal!",\
                                notification = "direct", \
                                log_message= "containerNameList is illegal!",\
                                response =  "please check params!")
            
        zkOper = Requests_ZkOpers()
        server_list = zkOper.retrieve_servers_white_list()
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        
        add_mem_result, ret = {}, {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/server/containers/memory/add' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args), connect_timeout=40, \
                                      request_timeout=40, auth_username = auth_username, auth_password = auth_password)
                
                response = yield Task(async_client.fetch, request)
                body = json.loads(response.body.strip())
                ret = body.get('response')
                add_mem_result.update(ret)
        finally:
            async_client.close()
            
        except_cons = list(set(container_name_list) - set(add_mem_result.keys()))
        for con in except_cons:
            add_mem_result.setdefault(con, 'no such container or code exception')
        self.finish(add_mem_result)


class UpdateServerClusterHandler(APIHandler):
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