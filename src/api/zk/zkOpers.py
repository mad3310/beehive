#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on 2013-7-11

@author: asus
'''

import logging
import threading

from kazoo.client import KazooClient, KazooState
from utils import ping_ip_available, nc_ip_port_available, get_zk_address
from kazoo.retry import KazooRetry
from utils.decorators import zk_singleton
from docker_letv.dockerOpers import Docker_Opers


class ZkOpers(object):
    
    zk = None
    
    rootPath = "/letv/docker"
    
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.zkaddress, self.zkport = get_zk_address()
        if "" != self.zkaddress and "" != self.zkport:
            
            self.DEFAULT_RETRY_POLICY = KazooRetry(
                max_tries=None,
                max_delay=10000,
            )
            self.zk = KazooClient(
                                  hosts=self.zkaddress+':'+str(self.zkport), 
                                  connection_retry=self.DEFAULT_RETRY_POLICY,
                                  timeout=20)
            self.zk.add_listener(self.listener)
            self.zk.start()
            logging.info("instance zk client (%s:%s)" % (self.zkaddress, self.zkport))


    def close(self):
        try:
            self.zk.stop()
            self.zk.close()
        except Exception, e:
            logging.error(e)
   
    def stop(self):
        try:
            self.zk.stop()
        except Exception, e:
            logging.error(e)
            raise

    def listener(self, state):
        if state == KazooState.LOST:
            logging.info("zk connect lost, stop this connection and then start new one!")
            
        elif state == KazooState.SUSPENDED:
            logging.info("zk connect suspended, stop this connection and then start new one!")
        else:
            pass

    def is_connected(self):
        return self.zk.state == KazooState.CONNECTED

    def re_connect(self):
        zk = KazooClient(hosts=self.zkaddress+':'+str(self.zkport), connection_retry=self.DEFAULT_RETRY_POLICY)
        zk.start()
        self.zk = zk
        return self.zk


    '''
    *****************************************************  uuid  *****************************************
    '''
      
    
    def writeClusterInfo(self, clusterUUID, clusterProps):
        path = self.rootPath + "/" + clusterUUID
        self.DEFAULT_RETRY_POLICY(self.zk.ensure_path, path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(clusterProps))
        
    def retrieveClusterProp(self, clusterUUID):
        resultValue = {}
        #clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID
        if self.DEFAULT_RETRY_POLICY(self.zk.exists, path):
            resultValue = self.DEFAULT_RETRY_POLICY(self.zk.get, path)
            
        return resultValue
    
    
    
    
    
    
    '''
    *****************************************************data node*****************************************
    '''
      
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

    def writeDataNodeInfo(self, clusterUUID, dataNodeProps):
        dataNodeIp = dataNodeProps['dataNodeIp']
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + dataNodeIp
        self.DEFAULT_RETRY_POLICY(self.zk.ensure_path, path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(dataNodeProps))
    
    def existDataNode(self, clusterUUID, dataNodeIp):
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + dataNodeIp
        self.zk.ensure_path(path)
        resultValue = self._retrieveSpecialPathProp(path)
        if resultValue:
            return True
        return False
    
    def writeDataNodeContainersResource(self, ip_address, resource_type, resource_info):
        _clusterUUID = self.getClusterUUID()
        _path = "%s/%s/dataNode/%s/containersResource/%s" % (self.rootPath, _clusterUUID, ip_address, resource_type)
        self.zk.ensure_path(_path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, _path, str(resource_info))

    def retrieveDataNodeContainersResource(self, ip_address, resource_type):
        _clusterUUID = self.getClusterUUID()
        _path = "%s/%s/dataNode/%s/containersResource/%s" % (self.rootPath, _clusterUUID, ip_address, resource_type)
        resultValue = self._retrieveSpecialPathProp(_path)
        return resultValue

    def writeDataNodeServerResource(self, ip_address, resource_info):
        _clusterUUID = self.getClusterUUID()
        _path = "%s/%s/dataNode/%s/serverResource" % (self.rootPath, _clusterUUID, ip_address)
        self.zk.ensure_path(_path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, _path, str(resource_info))

    def retrieveDataNodeServerResource(self, ip_address):
        _clusterUUID = self.getClusterUUID()
        _path = "%s/%s/dataNode/%s/serverResource" % (self.rootPath, _clusterUUID, ip_address)
        resultValue = self._retrieveSpecialPathProp(_path)
        return resultValue

    def retrieve_server_resource(self, host_ip, resource_type):
        cluster_uuid = self.getClusterUUID()
        path = self.rootPath + "/" + cluster_uuid + \
            "/dataNode/" + host_ip + "/resource/" + resource_type
        resultValue = self._retrieveSpecialPathProp(path)
        return resultValue
    
    '''
    *************************************container cluster****************************************
    '''
    
    def retrieve_cluster_list(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/"
        return self._return_children_to_list(path)
    
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
    
    def delete_container_cluster(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.DEFAULT_RETRY_POLICY(self.zk.delete, path, recursive=True)
        
    def write_container_cluster_info(self, containerClusterProps):
        containerClusterName = containerClusterProps['containerClusterName']
        cluster_info_before = self.retrieve_container_cluster_info(containerClusterName)
        cluster_info_before.update(containerClusterProps)
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(cluster_info_before))

    def write_container_node_value(self, cluster, container_node, containerProps):
        """write container node value not write status value
        
        """
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_node
        self.zk.ensure_path(path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(containerProps))

    def write_container_node_info(self, cluster, container_node, status, containerProps):
        """write container value and status value
         
        """
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_node
        logging.info('ensure_path : %s ' % path)
        self.zk.ensure_path(path)
        logging.info('set container node info')
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(containerProps))
        logging.info('set container node info done, check')
        
        stat = {}
        stat.setdefault('status', status)
        stat.setdefault('message', '')
        self.write_container_status(cluster, container_node, stat)

    def check_containerCluster_exists(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        if self.zk.exists(path):
            return True
        return False
    
    def write_container_status(self, cluster, container_node, record):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_node +"/status"
        self.zk.ensure_path(path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(record))

    def delete_container_node(self, cluster, container_node):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_node
        self.DEFAULT_RETRY_POLICY(self.zk.delete, path, recursive=True)    

    '''
    **************************************monitor status**************************************************
    '''

    def retrieve_monitor_status_list(self, monitor_type):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor/" + monitor_type
        monitor_status_type_list = self._return_children_to_list(path)
        return monitor_status_type_list
    
    def retrieve_monitor_status_value(self, monitor_type, monitor_key):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor/" + monitor_type + "/" + monitor_key
        resultValue = self._retrieveSpecialPathProp(path)
        return resultValue
    
    def retrieve_monitor_type(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor"
        monitor_type_list = self._return_children_to_list(path)
        return monitor_type_list
           
    def write_monitor_status(self, monitor_type, monitor_key, monitor_value):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor/" + monitor_type +"/"+ monitor_key
        logging.debug("monitor status:" + path)
        self.zk.ensure_path(path)
        self.DEFAULT_RETRY_POLICY(self.zk.set, path, str(monitor_value))#version need to write

    def retrieve_monitor_server_value(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor/server"
        resultValue = self._retrieveSpecialPathProp(path)
        return resultValue

    
    '''
    ***************************************config********************************************
    '''
    

    def retrieve_servers_white_list(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList"
        self.zk.ensure_path(path)
        data_node_ip_list = self._return_children_to_list(path)
        return data_node_ip_list
    
    def add_server_into_white_list(self, server_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList/" + server_ip 
        self.zk.ensure_path(path)

    def del_server_from_white_list(self, server_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/config/serversWhiteList/" + server_ip
        self.zk.ensure_path(path) 
        self.DEFAULT_RETRY_POLICY(self.zk.delete, path)



    '''
    **************ipPool*****************************************************************
    '''
    def recover_ips_to_pool(self, ip_list):
        clusterUUID = self.getClusterUUID()
        for ip in ip_list:
            path = self.rootPath + "/" + clusterUUID + "/ipPool" + "/" + ip
            self.zk.ensure_path(path)
            
    def retrieve_ip(self, ipCount):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/ipPool"
        rest_ip_list = self._return_children_to_list(path)
        assign_ip_list = []
        
        docker_opers = Docker_Opers()
        for ip in rest_ip_list:
            ippath = path + "/" + ip
            self.zk.delete(ippath)
            if not ping_ip_available(ip):
                host_con_ip_list = docker_opers.retrieve_containers_ips()
                if ip not in host_con_ip_list:
                    assign_ip_list.append(ip)
            if len(assign_ip_list) == ipCount:
                break
        return assign_ip_list
    
    def write_ip_into_ipPool(self, ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' +clusterUUID + '/ipPool/' + ip
        self.zk.ensure_path(path)
    
    def get_ips_from_ipPool(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' +clusterUUID + '/ipPool'
        return self._return_children_to_list(path)




   
            
    '''
    **********************************************Port Pool***********************************
    '''

    def retrieve_port(self, host_ip, port_count):
        clusterUUID = self.getClusterUUID()
        path = "%s/%s/portPool/%s" % (self.rootPath, clusterUUID, host_ip)
        rest_port_list = self._return_children_to_list(path)
        assign_port_list = []

        for port in rest_port_list:
            port_path = path + "/" + port
            self.DEFAULT_RETRY_POLICY(self.zk.delete, port_path)
            
            if not nc_ip_port_available(host_ip, port):
                assign_port_list.append(port)

            if len(assign_port_list) == port_count:
                break
        return assign_port_list

    def write_port_into_portPool(self, host_ip, port):
        clusterUUID = self.getClusterUUID()
        '''
        @todo: use %s%s way, don't use ++++
        '''
        path = self.rootPath + '/' + clusterUUID + "/portPool/" + host_ip + '/' + port
        self.zk.ensure_path(path)

    def get_ports_from_portPool(self, host_ip):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + '/' + clusterUUID + "/portPool/" + host_ip
        return self._return_children_to_list(path)

    '''
    *********************************************Lock**********************************************
    '''

    def lock_assign_ip(self):
        lock_name = "ip_assign"
        return self._lock_base_action(lock_name)
    
    def unLock_assign_ip(self, lock):
        self._unLock_base_action(lock)
        
    def lock_assign_port(self):
        lock_name = "port_assign"
        return self._lock_base_action(lock_name)
    
    def unLock_assign_port(self, lock):
        self._unLock_base_action(lock)
        
    def lock_async_monitor_action(self):
        lock_name = "async_monitor"
        return self._lock_base_action(lock_name)
    
    def unLock_aysnc_monitor_action(self, lock):
        self._unLock_base_action(lock)
        
    def lock_sync_server_zk_action(self):
        lock_name = "sync_server_zk"
        return self._lock_base_action(lock_name)
    
    def unLock_sync_server_zk_action(self, lock):
        self._unLock_base_action(lock)

    def lock_check_ip_usable_action(self):
        lock_name = "ip_usable"
        return self._lock_base_action(lock_name)
    
    def unLock_check_ip_usable_action(self, lock):
        self._unLock_base_action(lock)

    def lock_check_port_usable_action(self):
        lock_name = "port_usable"
        return self._lock_base_action(lock_name)
    
    def unLock_check_port_usable_action(self, lock):
        self._unLock_base_action(lock)

    '''
    *********************************************Base method*******************************************
    '''
            
    def _lock_base_action(self, lock_name):
        clusterUUID = self.getClusterUUID()
        path = "%s/%s/lock/%s" % (self.rootPath, clusterUUID, lock_name) 
        lock = self.DEFAULT_RETRY_POLICY(self.zk.Lock, path, threading.current_thread())
        isLock = lock.acquire(True, 1)
        return (isLock, lock)
        
    def _unLock_base_action(self, lock):
        if lock is not None:
            lock.release()
    
    def _return_children_to_list(self, path):
        logging.debug("check children:" + path)
        self.zk.ensure_path(path)
        children = self.DEFAULT_RETRY_POLICY(self.zk.get_children, path)
        
        children_to_list = []
        if len(children) != 0:
            for i in range(len(children)):
                children_to_list.append(children[i])
        return children_to_list
    
    def _retrieveSpecialPathProp(self,path):
        data = None
        
        if self.zk.exists(path):
            logging.debug(path+" existed")
            data,_ = self.DEFAULT_RETRY_POLICY(self.zk.get, path)
            
        logging.debug(data)
        
        resultValue = {}
        if data != None and data != '':
            resultValue = eval(data)
        return resultValue
    
    def getClusterUUID(self):
        dataNodeName = self.DEFAULT_RETRY_POLICY(self.zk.get_children, self.rootPath)
        return dataNodeName[0]
    
    def existCluster(self):
        self.zk.ensure_path(self.rootPath)
        clusters = self.DEFAULT_RETRY_POLICY(self.zk.get_children, self.rootPath)
        if len(clusters) != 0:
            return True
        return False


@zk_singleton
class Scheduler_ZkOpers(ZkOpers):
    
    def __init__(self):
        '''
        Constructor
        '''
        ZkOpers.__init__(self)


@zk_singleton
class Requests_ZkOpers(ZkOpers):
    
    def __init__(self):
        '''
        Constructor
        '''
        ZkOpers.__init__(self)


@zk_singleton
class Common_ZkOpers(ZkOpers):
    
    def __init__(self):
        '''
        Constructor
        '''
        ZkOpers.__init__(self) 


@zk_singleton
class Container_ZkOpers(ZkOpers):
    
    def __init__(self):
        '''
        Constructor
        '''
        ZkOpers.__init__(self)