#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import uuid
import json
import logging
import traceback
import urllib

from tornado.options import options
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.web import asynchronous
from tornado.gen import engine, Task
from common.configFileOpers import ConfigFileOpers
from common.serverOpers import Server_Opers
from common.tornado_basic_auth import require_basic_auth
from common.helper import _request_fetch, _retrieve_userName_passwd
from common.ipOpers import IpOpers
from common.serverClusterOpers import ServerCluster_Opers
from common.utils.autoutil import http_get
from common.utils.exceptions import HTTPAPIError
from handlers.base import APIHandler
from common.zkOpers import ZkOpers


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
        existCluster = self.zkOper.existCluster()
        if existCluster:
            clusterUUID = self.zkOper.getClusterUUID()
        else:
            clusterUUID = str(uuid.uuid1())
            requestParam.setdefault("clusterUUID", clusterUUID)
        if requestParam != {}:
            self.confOpers.setValue(options.server_cluster_property, requestParam)
            self.confOpers.setValue(options.data_node_property, requestParam)
          
        clusterProps = self.confOpers.getValue(options.server_cluster_property)
        dataNodeProprs = self.confOpers.getValue(options.data_node_property)
        self.zkOper.writeClusterInfo(clusterUUID, clusterProps)
        self.zkOper.writeDataNodeInfo(clusterUUID, dataNodeProprs)

        dataNodeIp = requestParam.get('dataNodeIp')
        existDataNode = self.zkOper.existDataNode(clusterUUID, dataNodeIp)
        
        if existDataNode:
            raise HTTPAPIError(status_code=417, error_detail="This machine has existed, no need to regedit!",\
                                notification = "direct", \
                                log_message= "Machine has been regedited!",\
                                response =  "This machine has been regedited!")
        
        dict = {}
        dict.setdefault("message", "creating server cluster successful!")
        self.finish(dict)
        
    def get(self):
        clusterUUID = self.zkOper.getClusterUUID()
        data, stat = self.zkOper.retrieveClusterProp(clusterUUID)
        self.confOpers.setValue(options.server_cluster_property, eval(data))
        
        dict = {}
        dict.setdefault("message", "sync server cluster info to local successful!")
        self.finish(dict)


@require_basic_auth
class GetServersInfoHandler(APIHandler):
    '''
    classdocs
    '''
    serverOpers = Server_Opers()
    
    
    def get(self):
        
        data_nodes_ip_list = self.zkOper.retrieve_data_node_list()
        uri = "/server"
        resource_dict = {}
        for data_node_ip in data_nodes_ip_list:
            requesturi = "http://%s:%s%s" % (data_node_ip, options.port, uri)
            retrun_dict = http_get(requesturi)
            resource_dict.setdefault(data_node_ip, retrun_dict['response'])
        
        self.finish(resource_dict)


@require_basic_auth
class UpdateServerClusterHandler(APIHandler):
    """
    update serverCluster 
    """
    
    serverCluster_opers = ServerCluster_Opers()
    
    def get(self):
        
        try:
            self.serverCluster_opers.update()
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="update server failed!",\
                                notification = "direct", \
                                log_message= 'update  server cluster failed' ,\
                                response =  "please check and notice related person")
        
        dict = {}
        dict.setdefault("message", "serverCluster update successful")
        self.finish(dict)
        

class AddServersMemoryHandler(APIHandler): pass


@require_basic_auth
class SwitchServersUnderoomHandler(APIHandler):
    
    @asynchronous
    @engine
    def post(self):
        
        args = self.get_all_arguments()
        switch = args.get('switch')
        
        if not switch or (switch!='on' and switch!='off'):
            raise HTTPAPIError(status_code=400, error_detail="switch params wrong!",\
                                notification = "direct", \
                                log_message= "switch params wrong!",\
                                response =  "please check params!")
        
        containerNameList = args.get('containerNameList')
        if not containerNameList:
            raise HTTPAPIError(status_code=400, error_detail="containerNameList params not given!",\
                                notification = "direct", \
                                log_message= "containerNameList params not given!",\
                                response =  "please check params!")
        
        server_list = self.zkOper.retrieve_servers_white_list()
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        
        result = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/server/containers/under_oom' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args), connect_timeout=40, \
                                      request_timeout=40, auth_username = auth_username, auth_password = auth_password)
                
                response = yield Task(async_client.fetch, request)
                body = json.loads( response.body.strip())
                ret =  body.get('response')
                result.update(ret)
        except:
            logging.error( str(traceback.format_exc() ) )
            raise HTTPAPIError(status_code=500, error_detail="switch server under_oom failed, action:%s!" % switch,\
                                notification = "direct", \
                                log_message= "switch server under_oom failed, action:%s!" % switch ,\
                                response =  "please check reasons")
        
        async_client.close()
        except_cons = list(set(container_name_list) - set(result.keys()))
        for con in except_cons:
            result.setdefault(con, 'no such container or code exception')
        self.finish( result )
    

@require_basic_auth
class GetherServersContainersDiskLoadHandler(APIHandler):
    
    zkOpers = ZkOpers('127.0.0.1', 2181)
    
    @asynchronous
    @engine
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        logging.info('get servers containers disk load method, containerNameList:%s' % str(containers) )
        container_name_list = containers.split(',')
        if not (container_name_list and isinstance(container_name_list, list)):
            raise HTTPAPIError(status_code=400, error_detail="containerNameList is illegal!",\
                                notification = "direct", \
                                log_message= "containerNameList is illegal!",\
                                response =  "please check params!")
        
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        server_list = self.zkOpers.retrieve_servers_white_list()

        servers_cons_disk_load, cons_disk_load = {}, {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/server/containers/disk' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args), connect_timeout=40, \
                                      request_timeout=40, auth_username = auth_username, auth_password = auth_password)
                
                response = yield Task(async_client.fetch, request)
                body = json.loads(response.body.strip())
                logging.info('response body : %s' % str(body) )
                cons_disk_load = body.get('response')
                servers_cons_disk_load.update(cons_disk_load)
        except:
            logging.error( str(traceback.format_exc() ) )
            raise HTTPAPIError(status_code=500, error_detail="get servers containers disk load fails",\
                                notification = "direct", \
                                log_message= "get servers containers disk load fails" ,\
                                response =  "please check reasons")
        
        async_client.close()
        self.finish( servers_cons_disk_load )


@require_basic_auth
class AddServersMemoryHandler(APIHandler):
    
    zkOpers = ZkOpers('127.0.0.1', 2181)
    
    @asynchronous
    @engine
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        logging.info('get servers containers disk load method, containerNameList:%s' % str(containers) )
        container_name_list = containers.split(',')
        if not (container_name_list and isinstance(container_name_list, list)):
            raise HTTPAPIError(status_code=400, error_detail="containerNameList is illegal!",\
                                notification = "direct", \
                                log_message= "containerNameList is illegal!",\
                                response =  "please check params!")
        
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        server_list = self.zkOpers.retrieve_servers_white_list()
        
        add_mem_result, ret = {}, {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/server/containers/memory/add' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args), connect_timeout=40, \
                                      request_timeout=40, auth_username = auth_username, auth_password = auth_password)
                
                response = yield Task(async_client.fetch, request)
                body = json.loads(response.body.strip())
                logging.info('response body : %s' % str(body) )
                ret = body.get('response')
                add_mem_result.update(ret)
        except:
            logging.error( str(traceback.format_exc() ) )
            raise HTTPAPIError(status_code=500, error_detail="add memory failed",\
                                notification = "direct", \
                                log_message= "add memory failed" ,\
                                response =  "please check reasons")
        
        async_client.close()
        except_cons = list(set(container_name_list) - set(add_mem_result.keys()))
        for con in except_cons:
            add_mem_result.setdefault(con, 'no such container or code exception')
        self.finish( add_mem_result )
