#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on 2013-7-11

@author: asus
'''

import logging
import threading
import traceback
import re
from utils.autoutil import *
from resourceOpers import Res_Opers
from kazoo.client import KazooClient

class ZkOpers(object):
    
    zk = None
    
    rootPath = "/letv/docker"
    
    '''
    classdocs
    '''
    def __init__(self,zkAddress,zkPort):
        '''
        Constructor
        '''
        logging.info("start zk")
        self.zk = KazooClient(hosts=zkAddress+':'+str(zkPort))
        self.zk.start()
        
    def existCluster(self):
        self.zk.ensure_path(self.rootPath)
        clusters = self.zk.get_children(self.rootPath)
        if len(clusters) != 0:
            return True
        return False
    
    def existDataNode(self, clusterUUID, dataNodeIp):
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + dataNodeIp
        self.zk.ensure_path(path)
        resultValue = self._retrieveSpecialPathProp(path)
        if resultValue:
            return True
        return False

    def getDataNodeNumber(self, clusterUUID):
        path = self.rootPath + "/" + clusterUUID
        dataNodeNumber = self.zk.get_children(path)
        return dataNodeNumber
    
    def getClusterUUID(self):
        logging.debug(self.rootPath)
        dataNodeName = self.zk.get_children(self.rootPath)
        logging.debug(dataNodeName)
        return dataNodeName[0]
      
    def retrieve_data_node_list(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/dataNode"
        data_node_ip_list = self._return_children_to_list(path)
        return data_node_ip_list
    
    def retrieve_data_node_info(self, ip_address):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + ip_address
        resultValue = self._retrieveSpecialPathProp(path)
        return resultValue

    def retrieve_servers_white_list(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList"
        self.zk.ensure_path(path)
        data_node_ip_list = self._return_children_to_list(path)
        return data_node_ip_list
    
    def retrieveClusterProp(self, clusterUUID):
        resultValue = {}
        #clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID
        if self.zk.exists(path):
            resultValue = self.zk.get(path)
            
        return resultValue

    def retrieve_container_num(self, containerClusterName):
        resultValue = self.retrieve_container_cluster_info(containerClusterName)
        return resultValue.get('containerCount')
    
    def retrieve_config_node_value(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config"
        return self._retrieveSpecialPathProp(path)       
    
    def retrieve_container_cluster_info(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        return self._retrieveSpecialPathProp(path)

    def retrieve_container_list(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        return self._return_children_to_list(path)
    
    def retrieve_container_node_value(self, containerClusterName, container_node):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName + '/' + container_node
        return self._retrieveSpecialPathProp(path)

    def retrieve_container_status_value(self, containerClusterName, container_node):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName + '/' + container_node + '/status'
        return self._retrieveSpecialPathProp(path)
    
    def retrieve_container_status_from_containerName(self, container_name):
        containerClusterName = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(containerClusterName, container_name)
        return self.retrieve_container_status_value(containerClusterName, container_ip)
        
    def retrieve_monitor_status_list(self, monitor_type):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/" + monitor_type
        monitor_status_type_list = self._return_children_to_list(path)
        return monitor_status_type_list
    
    def retrieve_monitor_status_value(self, monitor_type, monitor_key):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/" + monitor_type + "/" + monitor_key
        resultValue = self._retrieveSpecialPathProp(path)
        return resultValue
    
    def retrieve_monitor_type(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status"
        monitor_type_list = self._return_children_to_list(path)
        return monitor_type_list
        
    def retrieve_cluster_list(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/"
        return self._return_children_to_list(path)
    
    def recover_ips_to_pool(self, ip_list):
        clusterUUID = self.getClusterUUID()
        for ip in ip_list:
            path = self.rootPath + "/" + clusterUUID + "/ipPool" + "/" + ip
            self.zk.ensure_path(path)

    def retrieve_mcluster_info_from_config(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + '/config/normal'
        return self._retrieveSpecialPathProp(path)
    
    def retrieve_mclustervip_info_from_config(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + '/config/vip'
        return self._retrieveSpecialPathProp(path)
        
    def retrieve_ip(self, ipCount):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/ipPool"
        rest_ip_list = self._return_children_to_list(path)
        assign_ip_list = []

        for ip in rest_ip_list:
            ippath = path + "/" + ip
            self.zk.delete(ippath)
            if not ping_ip_able(ip):
                assign_ip_list.append(ip)
            if len(assign_ip_list) == ipCount:
                break
        return assign_ip_list
            
    def retrieve_started_nodes(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/node/started"
        started_nodes = self._return_children_to_list(path)
        return started_nodes
         
    def remove_started_node(self, data_node_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/node/started/" + data_node_ip
        if self.zk.exists(path):
            self.zk.delete(path)
           
    def write_monitor_status(self, monitor_type, monitor_key, monitor_value):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/" + monitor_type +"/"+ monitor_key
        logging.debug("monitor status:" + path)
        self.zk.ensure_path(path)
        self.zk.set(path, str(monitor_value))#version need to write

    def get_ips_from_ipPool(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' +clusterUUID + '/ipPool'
        return self._return_children_to_list(path)
   
    def remove_useless_ips(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/ipPool"
        ipPool_ip_list = self._return_children_to_list(path)
        
        res_opers = Res_Opers()
        host_con_ip_list = res_opers.get_containers_ip()
        
        ip_list = list( set(ipPool_ip_list) & set(host_con_ip_list) )
        for ip in ip_list:
            logging.info('delete ips from ipPools: %s for ip used' % str(ip) )
            _path = path + "/" + ip
            self.zk.delete(_path)

    def lock_assign_ip(self):
        lock_name = "ip_assign"
        return self._lock_base_action(lock_name)
    
    def unLock_assign_ip(self, lock):
        self._unLock_base_action(lock)
        
    def lock_async_monitor_action(self):
        lock_name = "async_monitor"
        return self._lock_base_action(lock_name)
    
    def unLock_aysnc_monitor_action(self, lock):
        self._unLock_base_action(lock)
            
    def _lock_base_action(self, lock_name):
        clusterUUID = self.getClusterUUID()
        path = "%s/%s/lock/%s" % (self.rootPath, clusterUUID, lock_name) 
        lock = self.zk.Lock(path, threading.current_thread())
        isLock = lock.acquire(True, 1)
        return (isLock, lock)
        
    def _unLock_base_action(self, lock):
        if lock is not None:
            lock.release()
    
    def _return_children_to_list(self, path):
        logging.debug("check children:" + path)
        self.zk.ensure_path(path)
        children = self.zk.get_children(path)
        
        children_to_list = []
        if len(children) != 0:
            for i in range(len(children)):
                children_to_list.append(children[i])
        return children_to_list
    
    def _retrieveSpecialPathProp(self,path):
        logging.debug(path)
        
        data = None
        
        if self.zk.exists(path):
            logging.debug(path+" existed")
            data,stat = self.zk.get(path)
            
        logging.debug(data)
        
        resultValue = {}
        if data != None and data != '':
            resultValue = eval(data)
        return resultValue
    
    def delete_container_cluster(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.zk.delete(path, recursive=True)
    
    def write_ip_into_ipPool(self, ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' +clusterUUID + '/ipPool/' + ip
        self.zk.ensure_path(path)
     
    def writeClusterNormalConf(self, info):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' + clusterUUID + '/config/normal'
        self.zk.ensure_path(path)
        self.zk.set(path, str(info))

    def writeClusterVipConf(self, info):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' + clusterUUID + '/config/vip'
        self.zk.ensure_path(path)
        self.zk.set(path, str(info))
                
    def writeClusterInfo(self, clusterUUID, clusterProps):
        path = self.rootPath + "/" + clusterUUID
        self.zk.ensure_path(path)
        self.zk.set(path, str(clusterProps))
             
    def writeDataNodeInfo(self, clusterUUID, dataNodeProps):
        dataNodeIp = dataNodeProps['dataNodeIp']
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + dataNodeIp
        self.zk.ensure_path(path)
        self.zk.set(path, str(dataNodeProps))
     
    def write_container_cluster_info(self, containerClusterProps):
        containerClusterName = containerClusterProps['containerClusterName']
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.zk.set(path, str(containerClusterProps))
            
    def write_container_node_info(self, status, containerProps):
        container_name = containerProps.get('container_name')
        cluster = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(cluster, container_name)
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_ip
        self.zk.ensure_path(path)
        self.zk.set(path, str(containerProps))
        self.write_container_status(cluster, container_ip, "{'status':'started', 'message':''}")
    
    def write_started_node(self, data_node_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/node/started/" + data_node_ip
        self.logger.debug("the started data node:" + data_node_ip)
        self.zk.ensure_path(path)

    def write_container_status(self, cluster, container_ip, record):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_ip +"/status"
        self.zk.ensure_path(path)
        self.zk.set(path, str(record))
    
    def write_container_status_by_containerName(self, container_name, record):
        containerClusterName = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(containerClusterName, container_name)
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName + "/" + container_ip +"/status"
        self.zk.ensure_path(path)
        self.zk.set(path, str(record))
    
    def get_containerIp(self, containerClusterName, container_name):
        con_ip = ''
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        container_ip_list = self.retrieve_container_list(containerClusterName)
        for container_ip in container_ip_list:
            container_info = self.retrieve_container_node_value(containerClusterName, container_ip)
            containerName = container_info.get('containerName')
            if container_name == containerName:
                con_ip = container_ip
                break
        return con_ip
    
    def check_containerCluster_exists(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        if self.zk.exists(path):
            return True
        return False

    def add_server_into_white_list(self, server_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList/" + server_ip 
        self.zk.ensure_path(path)

    def del_server_from_white_list(self, server_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList/" + server_ip
        self.zk.ensure_path(path) 
        self.zk.delete(path)
