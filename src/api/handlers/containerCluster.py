#!/usr/bin/env python
#-*- coding: utf-8 -*-

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
from common.containerClusterOpers import * 
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
        logging.info(' args:%s' % str(args))
        
        containerClusterName = args.get('containerClusterName')
        exists = self.zkOper.check_containerCluster_exists(containerClusterName)
        if exists:
            content = 'containerCluster %s has existed, choose another containerCluster name' % containerClusterName
            message = {'message' : content}
            self.finish(message)
            return
        
        error_msg = self.check_resource()
        if error_msg:
            raise HTTPAPIError(status_code=578, error_detail=error_msg,\
                                notification = "direct", \
                                log_message= error_msg,\
                                response =  "please add ips into pools")
        
        try:
            self.containerClusterOpers.create(args)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        dict = {} 
        dict.setdefault("message", "due to create container cluster need a little more times, please wait to finished and email to you, when cluster have started!")
        self.finish(dict)
    
    def delete(self):
        args = self.get_all_arguments()
        containerClusterName = args.get('containerClusterName')
        logging.info(' containerClusterName:%s' % containerClusterName)
        if not containerClusterName:
            raise HTTPAPIError(status_code=400, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        exists = self.zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            dict = {}
            dict.setdefault("message", "cluster has not existed, no need do this operation!")
            self.finish(dict)
            return

        try:
            self.containerClusterOpers.destory(containerClusterName)
        except:
            logging.error(str(traceback.format_exc()))
            raise HTTPAPIError(status_code=417, error_detail="containerCluster removed failed!",\
                                response =  "check if the containerCluster removed!")
      
        dict = {}
        dict.setdefault("message", "remove container has been done but need some time, please wait a little and check the result!")
        self.finish(dict)
    
    def check_resource(self):
        
        logging.info('remove useless ips')
        self.zkOper.remove_useless_ips()
        error_msg = ''
        ip_list = self.zkOper.get_ips_from_ipPool()
        if len(ip_list) < 4:
            error_msg = 'ips are not enough!'
        return error_msg

        
@require_basic_auth
class CheckCreateClusterStatusHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

    @asynchronous
    def get(self, containerClusterName):        
        try:
            check_result =  self.containerClusterOpers.check_create_status(containerClusterName)
        except:
            logging.error( str(traceback.format_exc()) )
        
        logging.info('check_result : %s' % (str(check_result), type(check_result)) )
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

    @asynchronous
    def get(self, containerClusterName):
        logging.info('containerClusterName:%s' % containerClusterName)
        
        exists = self.zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            status = {'status' : 'not exist'}
            self.finish(status)
            return
        
        try:
            check_result =  self.containerClusterOpers.check(containerClusterName)
        except kazoo.exceptions.LockTimeout:
            raise HTTPAPIError(status_code=578, error_detail="lock by other thread on assign ip processing",\
                                notification = "direct", \
                                log_message= "lock by other thread on assign ip processing",\
                                response =  "current operation is using by other people, please wait a moment to try again!")
        
        self.finish(check_result)


@require_basic_auth
class ContainerClusterStartHandler(APIHandler):
    '''
    classdocs
    '''
    containerClusterOpers = ContainerCluster_Opers()

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
        
        exists = self.zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise HTTPAPIError(status_code=400, error_detail="containerCluster %s not exist!" % containerClusterName,\
                                notification = "direct", \
                                log_message= "containerCluster %s not exist!" % containerClusterName,\
                                response =  "please check!")
        
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
        
        exists = self.zkOper.check_containerCluster_exists(containerClusterName)
        if not exists:
            raise HTTPAPIError(status_code=400, error_detail="containerCluster %s not exist!" % containerClusterName,\
                                notification = "direct", \
                                log_message= "containerCluster %s not exist!" % containerClusterName,\
                                response =  "please check!")
        
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


@require_basic_auth
class ContainerClustersInfoHandler(APIHandler):
    
    
    #curl "http://localhost:8888/clusters/info?cluster_name="""
    #curl "http://localhost:8888/clusters/info?cluster_name="abc""
    @asynchronous
    def get(self):
        
        cluster_info_collector = ClusterInfoCollector()
        clusters_zk_info =  cluster_info_collector.get_clusters_zk()
        
        if not clusters_zk_info:
            raise HTTPAPIError(status_code=-1, error_detail="There is not cluster in zookeeper",\
                            notification = "direct", \
                            log_message= "There is not cluster in zookeeper",\
                            response =  "There is not cluster in zookeeper")
        
        self.finish(clusters_zk_info)


@require_basic_auth
class ContainerClusterInfoHandler(APIHandler):
    
    #curl "http://localhost:8888/clusters/info?cluster_name="""
    #curl "http://localhost:8888/clusters/info?cluster_name="abc""
    @asynchronous
    def get(self, containerClusterName):
        
        if not containerClusterName:
            raise HTTPAPIError(status_code=400, error_detail="no containerClusterName argument!",\
                                notification = "direct", \
                                log_message= "no containerClusterName argument!",\
                                response =  "please check params!")
        
        cluster_info_collector = ClusterInfoCollector()
        cluster_zk_info =  cluster_info_collector.get_cluster_zk(containerClusterName)      
        
        if not cluster_zk_info:
            raise HTTPAPIError(status_code=500, error_detail="There is no cluster info in zookeeper",\
                            notification = "direct", \
                            log_message= "There is  no cluster info in zookeeper",\
                            response =  "There is no cluster info in zookeeper")

        self.finish(cluster_zk_info)


@require_basic_auth
class CheckClusterSyncHandler(APIHandler):

    @asynchronous
    def get(self):
        try:
            get_cluster_changes = GetClustersChanges()
            res_info =  get_cluster_changes.get_res()      
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="code error!",\
                            notification = "direct", \
                            log_message= "code error!",\
                            response =  "code error!")
        
        dict = {}
        logging.info('data:%s' % str(res_info))
        dict.setdefault('data', res_info)
        self.finish(dict)
        
