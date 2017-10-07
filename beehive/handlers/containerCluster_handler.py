#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Created on Sep 8, 2014

@author: root
'''
import logging
import urllib
import json

from tornado.options import options
from tornado.web import asynchronous
from tornadoForBeehive.tornado_basic_auth import require_basic_auth
from base import APIHandler
from utils.exceptions import HTTPAPIError, UserVisiableException
from containerCluster.containerClusterOpers import ContainerCluster_Opers
from zk.zkOpers import Requests_ZkOpers
from tornado.gen import engine, Task
from utils import _retrieve_userName_passwd
from tornado.httpclient import HTTPRequest, AsyncHTTPClient


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
        
        self.containerClusterOpers.create(args)
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
class CheckContainerClusterCreateResultHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()
    
    # eg. curl --user root:root -X GET http://10.154.156.150:8888/containerCluster/status/dh
    def get(self, containerClusterName):
        result = self.containerClusterOpers.create_result(containerClusterName)
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


@require_basic_auth
class SetContainerClusterCpusharesHandler(APIHandler):
    
    @asynchronous
    @engine
    def post(self):
        args = self.get_all_arguments()
        cluster = args.get('containerClusterName')
        if not cluster:
            raise UserVisiableException("params containerClusterName should be given!")
        
        zkOper = Requests_ZkOpers()
        exists = zkOper.check_containerCluster_exists(cluster)
        if not exists:
            raise UserVisiableException('containerCluster %s not exist, choose another containerCluster name' % cluster)
        times = args.get('times')
        if not times:
            raise UserVisiableException("params times should be given!")        
        
        hostIp_containerName_list = self.__get_hostIp_containerName_list(cluster)
        auth_username, auth_password = _retrieve_userName_passwd()
        async_client = AsyncHTTPClient()
        
        _post_args, set_cpushares_result = {}, {}
        _post_args.setdefault('times', times)
        try:
            for host_ip, container_name in hostIp_containerName_list:
                requesturi = 'http://%s:%s/container/cpushares' % (host_ip, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                _post_args.update({'containerName':container_name})
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(_post_args), connect_timeout=40, \
                                      request_timeout=40, auth_username = auth_username, auth_password = auth_password)
                
                response = yield Task(async_client.fetch, request)
                body = json.loads(response.body.strip())
                ret = body.get('response')
                set_cpushares_result.update(ret)
        finally:
            async_client.close()
        
        self.finish(set_cpushares_result)

    def __get_hostIp_containerName_list(self, cluster):
        zkOper = Requests_ZkOpers()
        hostIp_containerName_list = []
        container_list = zkOper.retrieve_container_list(cluster)
        for container in container_list:
            container_info = zkOper.retrieve_container_node_value(cluster, container)
            host_ip = container_info.get('hostIp')
            container_name =  container_info.get('containerName')
            hostIp_containerName_list.append((host_ip, container_name))
        return hostIp_containerName_list


@require_basic_auth
class ContainerClusterNodeHandler(APIHandler):
    '''
    classdocs
    '''
    cluster_opers = ContainerCluster_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        container_names = self.cluster_opers.add(args)
        result = {}
        result.setdefault('containerNames', container_names)
        result.setdefault("message", "due to add container need a little more times, please wait a moment and check the result!")
        self.finish(result)
    
    # eg. curl --user root:root "http://127.0.0.1:8888/containerCluster/zz/node/d-mcl-zz-n-5,d-mcl-zz-n-4"
    def get(self, cluster, _container_names):
        container_names = _container_names.split(',')
        container_info = self.cluster_opers.create_result(cluster, container_names)
        
        self.finish(container_info)


@require_basic_auth
class ContainerClusterRemoveNodeHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        
        self.containerClusterOpers.remove(args)
        result = {}
        result.setdefault("message", "remove container will take a few seconds,please wait!")
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

