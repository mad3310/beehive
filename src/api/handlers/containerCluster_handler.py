#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Created on Sep 8, 2014

@author: root
'''
import kazoo
import logging

from tornado.web import asynchronous
from tornado_letv.tornado_basic_auth import require_basic_auth
from base import APIHandler
from utils.exceptions import HTTPAPIError
from container.containerOpers import Container_Opers
from containerCluster.containerClusterOpers import ContainerCluster_Opers
from zk.zkOpers import ZkOpers


class GatherClusterResourceHandler(APIHandler):
    '''
        the result is webportal need, return to webportal
    '''
    
    container_opers = Container_Opers()
    
    def cluster_resoure(self, cluster, resource_type):
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
            host_container_dict, result  = {}, []
            for container_node in container_node_list:
                container_name = self.container_opers.get_container_name_from_zk(cluster, container_node)
                host_ip = self.container_opers.get_host_ip_from_zk(cluster, container_node)
                host_container_dict.setdefault(host_ip, container_name)
            
            for host_ip, container_name in host_container_dict.items():
                resource = {}
                resource_info = zkOper.retrieveDataNodeContainersResource(host_ip, resource_type)
                container_resource = resource_info.get(resource_type)
                _resource = container_resource.get(container_name)
                resource.setdefault('value', _resource)
                resource.setdefault('hostIp', host_ip)
                resource.setdefault('containerName', container_name)
                result.append(resource)
        finally:
            zkOper.close()
        
        return result


class GatherClusterMemeoyHandler(GatherClusterResourceHandler):
    
    def get(self, cluster):
        result = self.cluster_resoure(cluster, 'memory')
        self.finish({'data': result})


class GatherClusterCpuacctHandler(GatherClusterResourceHandler):

    def get(self, cluster):
        result = self.cluster_resoure(cluster, 'cpuacct')
        self.finish({'data': result})


class GatherClusterNetworkioHandler(GatherClusterResourceHandler):
        
    def get(self, cluster):
        result = self.cluster_resoure(cluster, 'networkio')
        self.finish({'data': result})


class GatherClusterDiskHandler(GatherClusterResourceHandler):
        
    def get(self, cluster):
        result = self.cluster_resoure(cluster, 'disk')
        self.finish({'data': result})


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

