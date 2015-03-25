#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import kazoo
import logging
import traceback
import json

from tornado.web import asynchronous
from tornado.gen import engine, Task
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.options import options
from tornado_letv.tornado_basic_auth import require_basic_auth
from base import APIHandler
from utils import _retrieve_userName_passwd
from utils.exceptions import HTTPAPIError
from containerCluster.containerClusterOpers import ContainerCluster_Opers, GetLastestClustersInfo


@require_basic_auth
class GatherClusterNetworkioHandler(APIHandler):
    '''
    classdocs
    '''
    
    # eg . curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/networkio
    @asynchronous
    @engine
    def get(self, cluster):
        logging.info(cluster)
        exists = self.zkOper.check_containerCluster_exists(cluster)
        if not exists:
            content = 'container cluster %s not exist, please check your cluster name' % cluster
            message = {'message' : content}
            self.finish(message)
            return
         
        container_dict, result = {}, {}
        container_ip_list = self.zkOper.retrieve_container_list(cluster)
        for container_ip in container_ip_list:
            container_name = self.zkOper.get_containerName(cluster, container_ip)
            host_ip = self.zkOper.get_hostIp(cluster, container_ip)
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
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/memory
    @asynchronous
    @engine
    def get(self, cluster):
        logging.info(cluster)
        exists = self.zkOper.check_containerCluster_exists(cluster)
        if not exists:
            content = 'container cluster %s not exist, please check your cluster name' % cluster
            message = {'message' : content}
            self.finish(message)
            return
        
        container_dict, result = {}, {}
        container_ip_list = self.zkOper.retrieve_container_list(cluster)
        for container_ip in container_ip_list:
            container_name = self.zkOper.get_containerName(cluster, container_ip)
            host_ip = self.zkOper.get_hostIp(cluster, container_ip)
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
class GatherClusterCpuacctHandler(APIHandler):
    '''
    classdocs
    '''
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/container/stat/d-mcl-test_jll-n-1/cpuacct
    @asynchronous
    @engine
    def get(self, cluster):
        logging.info(cluster)

        exists = self.zkOper.check_containerCluster_exists(cluster)
        if not exists:
            content = 'container cluster %s not exist, please check your cluster name' % cluster
            message = {'message' : content}
            self.finish(message)
            return

        container_dict, result = {}, {}
        container_ip_list = self.zkOper.retrieve_container_list(cluster)
        for container_ip in container_ip_list:
            container_name = self.zkOper.get_containerName(cluster, container_ip)
            host_ip = self.zkOper.get_hostIp(cluster, container_ip)
            container_dict.setdefault(host_ip, container_name)
        
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        for host_ip, container_name in container_dict.items():
            requesturi = 'http://%s:%s/container/stat/%s/cpuacct' % (host_ip, options.port, container_name)
            logging.info('cpuacct requesturi: %s' % str(requesturi))
            request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40, request_timeout=40, \
                                  auth_username = auth_username, auth_password = auth_password)
            
            response = yield Task(async_client.fetch, request)
            body = json.loads(response.body.strip())
            ret = body.get('response')
            result.update({host_ip:ret})
        
        async_client.close()
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
        logging.info(' args:%s' % str(args))
        
        try:
            self.containerClusterOpers.create(args)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        return_message = {} 
        return_message.setdefault("message", "due to create container cluster need a little more times, please wait to finished and email to you, when cluster have started!")
        self.finish(return_message)

    # eg. curl --user root:root -X DELETE http://10.154.156.150:8888/containerCluster?containerClusterName=dh
    def delete(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        logging.info(' containerClusterName:%s' % containerClusterName)
        self.containerClusterOpers.destory(containerClusterName)
        
        return_message = {}
        return_message.setdefault("message", "remove container has been done but need some time, please wait a moment and check the result!")
        self.finish(return_message)


@require_basic_auth
class CheckCreateClusterStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # eg. curl --user root:root -X GET http://localhost:8888/containerCluster/createStatus/dh
    def get(self, containerClusterName):        
        check_result = ''
        check_result =  self.containerClusterOpers.create_status(containerClusterName)
        
        logging.info('check_result : %s, type: %s' % (str(check_result), type(check_result)) )
        if check_result.get('code') == '000002':
            error_message = check_result.get('error_msg')
            raise HTTPAPIError(status_code=579, error_detail=error_message,\
                                notification = "direct", \
                                log_message= error_message)
        
        self.finish(check_result)


@require_basic_auth
class CheckContainerClusterStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/containerCluster/status/dh
    def get(self, containerClusterName):
        
        check_result =  self.containerClusterOpers.check(containerClusterName)
        '''
        @todo: no need to check zk locktimeout?
        '''
#        try:
#            check_result =  self.containerClusterOpers.check(containerClusterName)
#        except kazoo.exceptions.LockTimeout:
#            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
#                                notification = "direct", \
#                                log_message= "lock by other thread on assign ip processing",\
#                                response =  "current operation is using by other people, please wait a moment to try again!")
        self.finish(check_result)


@require_basic_auth
class ContainerClusterStartHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    # eg. curl --user root:root -d "containerClusterName=dj" http://10.154.156.150:8888/containerCluster/start
    @asynchronous
    def post(self):
        logging.info('containerClusterName')
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        logging.info('containerClusterName:%s' % containerClusterName)
        if not containerClusterName:
            raise HTTPAPIError(status_code=400, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        try:
            self.containerClusterOpers.start(containerClusterName)
        except:
            raise HTTPAPIError(status_code=578, error_detail="start container cluster failed",\
                                notification = "direct", \
                                log_message= "start container cluster failed",\
                                response =  "start container cluster failed, please check!")
        
        massage = {}
        massage.setdefault("message", "due to start a container cluster need a lot time, please wait and check the result~")
        self.finish(massage)


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
            raise HTTPAPIError(status_code=400, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        try:
            self.containerClusterOpers.stop(containerClusterName)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=578, error_detail="stop container cluster failed",\
                                notification = "direct", \
                                log_message= "stop container cluster failed",\
                                response =  "stop container cluster failed, please check!")
        
        massage = {}
        massage.setdefault("message", "due to stop a container cluster need a lot time, please wait and check the result~")
        self.finish(massage)

@require_basic_auth
class ClusterConfigHandler(APIHandler):
    
    containerClusterOpers = ContainerCluster_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        logging.info('config args:%s' % str(args))
        error_msg = self.containerClusterOpers.config(args)
        if error_msg:
            raise HTTPAPIError(status_code=500, error_detail=error_msg,\
                               response =  "please check if params correct")
        
        return_message = {}
        return_message.setdefault("message", "write config infomation successfully!")
        self.finish(return_message)


@require_basic_auth
class ContainerClustersInfoHandler(APIHandler):
    
    container_cluster_opers = ContainerCluster_Opers()
    
    #curl "http://localhost:8888/clusters/info?cluster_name="""
    #curl "http://localhost:8888/clusters/info?cluster_name="abc""
    
    def get(self):
        
        clusters_zk_info =  self.container_cluster_opers.get_clusters_zk()
        
        if not clusters_zk_info:
            raise HTTPAPIError(status_code=417, error_detail="There is not cluster in zookeeper",\
                               notification = "direct", \
                               log_message= "There is not cluster in zookeeper",\
                               response =  "There is not cluster in zookeeper")
        
        self.finish(clusters_zk_info)


@require_basic_auth
class ContainerClusterInfoHandler(APIHandler):
    
    container_cluster_opers = ContainerCluster_Opers()
    #curl "http://localhost:8888/clusters/info?cluster_name="""
    #curl "http://localhost:8888/clusters/info?cluster_name="abc""
    @asynchronous
    def get(self, containerClusterName):
        
        if not containerClusterName:
            raise HTTPAPIError(status_code=417, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        
        cluster_zk_info =  self.container_cluster_opers.get_cluster_zk(containerClusterName)      
        
        if not cluster_zk_info:
            raise HTTPAPIError(status_code=417, error_detail="There is no cluster info in zookeeper",\
                            notification = "direct", \
                            log_message= "There is  no cluster info in zookeeper",\
                            response =  "There is no cluster info in zookeeper")

        self.finish(cluster_zk_info)


@require_basic_auth
class CheckClusterSyncHandler(APIHandler):

    get_cluster_changes = GetLastestClustersInfo()
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/containerCluster/sync
    def get(self):
        res_info =  self.get_cluster_changes.get_res()
        return_message = {}
        logging.info('data:%s' % str(res_info))
        return_message.setdefault('data', res_info)
        self.finish(return_message)

