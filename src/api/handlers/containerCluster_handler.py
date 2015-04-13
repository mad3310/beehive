#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Created on Sep 8, 2014

@author: root
'''
import kazoo
import logging
import json

from tornado.web import asynchronous
from tornado.gen import engine, Task
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.options import options
from tornado_letv.tornado_basic_auth import require_basic_auth
from base import APIHandler
from utils import _retrieve_userName_passwd
from utils.exceptions import HTTPAPIError
from container.containerOpers import Container_Opers
from containerCluster.containerClusterOpers import ContainerCluster_Opers
from zk.zkOpers import ZkOpers


@require_basic_auth
class GatherClusterNetworkioHandler(APIHandler):
    '''
    classdocs
    '''
    '''
    @todo: 
    1. same as GatherClusterNetworkioHandler, GatherClusterMemeoyHandler, GatherClusterCpuacctHandler, need abstract to base logic.
    2. use scheduler_tesk to put these data to zk, these interface only retrieve data from zk and returned.
    '''
    container_opers = Container_Opers()
    
    # eg . curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/networkio
    @asynchronous
    @engine
    def get(self, cluster):
        zkOper = ZkOpers()
        
        try:
            exists = zkOper.check_containerCluster_exists(cluster)
            if not exists:
                error_message = 'container cluster %s not exist, please check your cluster name' % cluster
                raise HTTPAPIError(status_code=417, error_detail=error_message,\
                                    notification = "direct", \
                                    log_message= error_message,\
                                    response =  error_message)
                
            container_node_list = zkOper.retrieve_container_list(cluster)
        finally:
            zkOper.close()
         
        container_dict, result = {}, {}
        for container_ip in container_node_list:
            container_name = self.container_opers.get_container_name_from_zk(cluster, container_ip)
            host_ip = self.container_opers.get_host_ip_from_zk(cluster, container_ip)
            container_dict.setdefault(host_ip, container_name)
         
        auth_username, auth_password = _retrieve_userName_passwd()
         
        async_client = AsyncHTTPClient()
        for host_ip, container_name in container_dict.items():
            requesturi = 'http://%s:%s/container/stat/%s/networkio' % (host_ip, options.port, container_name)
            logging.info('memory stat requesturi: %s' % str(requesturi))
            request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40, request_timeout=40, \
                                  auth_username = auth_username, auth_password = auth_password)
             
            response = yield Task(async_client.fetch, request)
            body = json.loads(response.body.strip())
            ret = body.get('response')
            result.update({host_ip:ret})
         
        async_client.close()
        self.finish(result)


@require_basic_auth
class GatherClusterMemeoyHandler(APIHandler):
    '''
    classdocs
    '''
    
    container_opers = Container_Opers()
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/memory
    @asynchronous
    @engine
    def get(self, cluster):
        zkOper = ZkOpers()
        
        try:
            exists = zkOper.check_containerCluster_exists(cluster)
            if not exists:
                error_message = 'container cluster %s not exist, please check your cluster name' % cluster
                raise HTTPAPIError(status_code=417, error_detail=error_message,\
                                    notification = "direct", \
                                    log_message= error_message,\
                                    response =  error_message)
                
            container_node_list = zkOper.retrieve_container_list(cluster)
        finally:
            zkOper.close()
        
        container_dict, result = {}, {}
        for container_ip in container_node_list:
            container_name = self.container_opers.get_container_name_from_zk(cluster, container_ip)
            host_ip = self.container_opers.get_host_ip_from_zk(cluster, container_ip)
            container_dict.setdefault(host_ip, container_name)
        
        auth_username, auth_password = _retrieve_userName_passwd()
        
        async_client = AsyncHTTPClient()
        for host_ip, container_name in container_dict.items():
            requesturi = 'http://%s:%s/container/stat/%s/memory' % (host_ip, options.port, container_name)
            logging.info('memory stat requesturi: %s' % str(requesturi))
            request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40, request_timeout=40, \
                                  auth_username = auth_username, auth_password = auth_password)
            
            response = yield Task(async_client.fetch, request)
            body = json.loads(response.body.strip())
            ret = body.get('response')
            result.update({host_ip:ret})
        
        async_client.close()
        self.finish(result)


@require_basic_auth
class GatherClusterResourceHandler(APIHandler):
    '''
    classdocs
    '''
    
    container_opers = Container_Opers()
    
    def __init__(self, resource_type):
        self.resource_type = resource_type
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/cpuacct
    @asynchronous
    @engine
    def get(self, cluster):
        zkOper = ZkOpers()
        
        try:
            exists = zkOper.check_containerCluster_exists(cluster)
            if not exists:
                error_message = 'container cluster %s not exist, please check your cluster name' % cluster
                raise HTTPAPIError(status_code=417, error_detail=error_message,\
                                    notification = "direct", \
                                    log_message= error_message,\
                                    response =  error_message)
            
            container_node_list = zkOper.retrieve_container_list(cluster)
            container_dict, result = {}, {}
            for container_node in container_node_list:
                container_name = self.container_opers.get_container_name_from_zk(cluster, container_node)
                host_ip = self.container_opers.get_host_ip_from_zk(cluster, container_node)
                container_dict.setdefault(host_ip, container_name)
            
            for host_ip, container_name in container_dict.items():
                resource_info = zkOper.retrieveDataNodeContainersResource(host_ip, self.resource_type)
                
        finally:
            zkOper.close()
        
        self.finish(result)


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
        result = {} 
        result.setdefault("message", "due to create container cluster need a little more times, please wait to finished and email to you, when cluster have started!")
        self.finish(result)

    # eg. curl --user root:root -X DELETE http://10.154.156.150:8888/containerCluster?containerClusterName=dh
    def delete(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        self.containerClusterOpers.destory(containerClusterName)
        
        result = {}
        result.setdefault("message", "delete container has been done but need some time, please wait a moment and check the result!")
        self.finish(result)
    
    #eg. curl --user root:root "http://localhost:8888/containerCluster"
    #eg. curl --user root:root "http://localhost:8888/containerCluster?containerClusterName='abc'"
    def get(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        
        if containerClusterName is not None:
            clusters_zk_info = self.container_cluster_opers.get_cluster_zk(containerClusterName)
        else:
            clusters_zk_info =  self.containerClusterOpers.get_clusters_zk()
        
        if not clusters_zk_info:
            raise HTTPAPIError(status_code=417, error_detail="There is not cluster in zookeeper",\
                               notification = "direct", \
                               log_message= "There is not cluster in zookeeper",\
                               response =  "There is not cluster in zookeeper")
        
        self.finish(clusters_zk_info)


@require_basic_auth
class CheckCreateClusterStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # eg. curl --user root:root -X GET http://localhost:8888/containerCluster/createStatus/dh
    def get(self, containerClusterName):
        result =  self.containerClusterOpers.check(containerClusterName)
        
        logging.info('check_result : %s, type: %s' % (str(result), type(result)))
        if result.get('code') == '000002':
            error_message = result.get('error_msg')
            raise HTTPAPIError(status_code=417, error_detail=error_message,\
                                notification = "direct", \
                                log_message= error_message)
        
        self.finish(result)


@require_basic_auth
class CheckContainerClusterStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/containerCluster/status/dh
    def get(self, containerClusterName):
        result = self.containerClusterOpers.check(containerClusterName)
        self.finish(result)


@require_basic_auth
class ContainerClusterStartHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # eg. curl --user root:root -d "containerClusterName=dj" http://10.154.156.150:8888/containerCluster/start
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        logging.info('containerClusterName:%s' % containerClusterName)
        if not containerClusterName:
            raise HTTPAPIError(status_code=417, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        self.containerClusterOpers.start(containerClusterName)
        
        result = {}
        result.setdefault("message", "due to start a container cluster need a lot time, please wait and check the result~")
        self.finish(result)


@require_basic_auth
class ContainerClusterStopHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # eg. curl --user root:root -d "containerClusterName=dj" http://10.154.156.150:8888/containerCluster/stop
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        logging.info('containerClusterName:%s' % containerClusterName)
        if not containerClusterName:
            raise HTTPAPIError(status_code=417, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        self.containerClusterOpers.stop(containerClusterName)
        
        result = {}
        result.setdefault("message", "due to stop a container cluster need a lot time, please wait and check the result~")
        self.finish(result)

@require_basic_auth
class ClusterConfigHandler(APIHandler):
    
    containerClusterOpers = ContainerCluster_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        logging.info('config args:%s' % str(args))
        error_msg = self.containerClusterOpers.config(args)
        if error_msg:
            raise HTTPAPIError(status_code=417, error_detail=error_msg,\
                               response =  "please check if params correct")
        
        result = {}
        result.setdefault("message", "write config infomation successfully!")
        self.finish(result)


@require_basic_auth
class CheckClusterSyncHandler(APIHandler):
    
    container_cluster_opers = ContainerCluster_Opers()
    
    """
        webportal do info sync every 10 minutes,
        then interface will invoke this class
    """
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/containerCluster/sync
    def get(self):
        _clusterInfo =  self.container_cluster_opers.sync()
        logging.info('data:%s' % str(_clusterInfo))
        
        result = {}
        result.setdefault('data', _clusterInfo)
        self.finish(result)

