#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on 2013-7-11

@author: asus
'''

import logging
import threading

from docker_letv.dockerOpers import Docker_Opers
from kazoo.client import KazooClient
from container.container_module import Container
from utils.autoutil import get_containerClusterName_from_containerName
from utils.autoutil import ping_ip_able
from utils.autoutil import nc_ip_port_available
from utils.decorators import singleton

'''
@todo: need to check every method is should be now.
'''

@singleton
class ZkOpers(object):
    
    zk = None
    
    rootPath = "/letv/docker"
    
    docker_opers = Docker_Opers()
    
    '''
    classdocs
    '''
    def __init__(self, zkAddress='127.0.0.1', zkPort=2181):
        '''
        Constructor
        '''
        logging.info("start zk")
        self.zk = KazooClient(hosts=zkAddress+':'+str(zkPort))
        self.zk.start()
    
    def close(self):
        self.zk.close()
    
    def writeClusterInfo(self, clusterUUID, clusterProps):
        path = self.rootPath + "/" + clusterUUID
        self.zk.ensure_path(path)
        self.zk.set(path, str(clusterProps))
        
    def retrieveClusterProp(self, clusterUUID):
        resultValue = {}
        #clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID
        if self.zk.exists(path):
            resultValue = self.zk.get(path)
            
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
        self.zk.ensure_path(path)
        self.zk.set(path, str(dataNodeProps))
    
    def existDataNode(self, clusterUUID, dataNodeIp):
        path = self.rootPath + "/" + clusterUUID + "/dataNode/" + dataNodeIp
        self.zk.ensure_path(path)
        resultValue = self._retrieveSpecialPathProp(path)
        if resultValue:
            return True
        return False
    

    
    
    
    
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

    '''
    @todo: move to containerOpers or containerClusterOpers?
    '''
    def retrieve_container_node_value_from_containerName(self, container_name):
        cluster = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(cluster, container_name)
        return self.retrieve_container_node_value(cluster, container_ip)

    def retrieve_container_status_value(self, containerClusterName, container_node):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName + '/' + container_node + '/status'
        return self._retrieveSpecialPathProp(path)
    
    def delete_container_cluster(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.zk.delete(path, recursive=True)
        
    def write_container_cluster_info(self, containerClusterProps):
        containerClusterName = containerClusterProps['containerClusterName']
        cluster_info_before = self.retrieve_container_cluster_info()
        cluster_info_before.update(containerClusterProps)
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        self.zk.set(path, str(cluster_info_before))

    def write_container_node_value(self, cluster, container_ip, containerProps):
        """write container node value not write status value
        
        """
        
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_ip
        self.zk.ensure_path(path)
        self.zk.set(path, str(containerProps))
    
    '''
    @todo: move to containerOpers or containerClusterOpers?
    '''
    def retrieve_container_status_from_containerName(self, container_name):
        containerClusterName = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(containerClusterName, container_name)
        return self.retrieve_container_status_value(containerClusterName, container_ip)
    
    '''
    @todo: move this method to containerOpers or containerClusterOpers?
    '''
    def write_container_node_value_by_containerName(self, container_name, containerProps):
        """only write container value and not write status value
        
        """
        
        cluster = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(cluster, container_name)
        self.write_container_node_value(cluster, container_ip, containerProps)

    
    def write_container_node_info(self, status, containerProps):
        """write container value and status value
        
        """
        
        '''
        @todo: put other issues to containerOpers or containerClusterOpers?
        '''
        inspect = containerProps.get('inspect')
        is_use_ip =  containerProps.get('isUseIp')
        con = Container(inspect=inspect)
        container_name = con.name()
        cluster = con.cluster(container_name)
        logging.info('get container cluster :%s' % cluster)
        if is_use_ip:
            container_ip = con.ip()
            logging.info('get container ip :%s' % container_ip)
            if not (container_ip and cluster):
                logging.error('get container ip or cluster name failed, not write this info')
                logging.info('inspect : %s' % str(inspect) )
                return
            container_node = container_ip
        else:
            container_node = container_name
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_node
        self.zk.ensure_path(path)
        self.zk.set(path, str(containerProps))
        stat = {}
        stat.setdefault('status', status)
        stat.setdefault('message', '')
        self.__write_container_status(cluster, container_node, stat)
    
    def check_containerCluster_exists(self, containerClusterName):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        if self.zk.exists(path):
            return True
        return False
    
    def __write_container_status(self, cluster, container_ip, record):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + cluster + "/" + container_ip +"/status"
        self.zk.ensure_path(path)
        self.zk.set(path, str(record))
        
    '''
    @todo: put this method into containerOpers or containerClusterOpers?
    '''
    def get_containerIp(self, containerClusterName, container_name):
        con_ip = ''
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/container/cluster/" + containerClusterName
        self.zk.ensure_path(path)
        container_ip_list = self.retrieve_container_list(containerClusterName)
        for container_ip in container_ip_list:
            container_info = self.retrieve_container_node_value(containerClusterName, container_ip)
            inspect = container_info.get('inspect')
            con = Container(inspect=inspect)
            con_name = con.name()
            if container_name == con_name:
                con_ip = container_ip
                break
        return con_ip





    
    '''
    **************************************monitor status**************************************************
    '''    
    '''
    @todo: every container_node has status item, what is the monitor_status?
    '''
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
           
    def write_monitor_status(self, monitor_type, monitor_key, monitor_value):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/monitor_status/" + monitor_type +"/"+ monitor_key
        logging.debug("monitor status:" + path)
        self.zk.ensure_path(path)
        self.zk.set(path, str(monitor_value))#version need to write





    
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
        self.zk.delete(path)





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

        for ip in rest_ip_list:
            ippath = path + "/" + ip
            self.zk.delete(ippath)
            if not ping_ip_able(ip):
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
    
    
    def remove_useless_ips(self):
        clusterUUID = self.getClusterUUID()
        path = self.rootPath + "/" + clusterUUID + "/ipPool"
        ipPool_ip_list = self._return_children_to_list(path)
        
        '''
        @todo: should not put more logic into zkOpers
        '''
        host_con_ip_list = self.docker_opers.retrieve_containers_ips()
        
        ip_list = list( set(ipPool_ip_list) & set(host_con_ip_list) )
        for ip in ip_list:
            logging.info('delete ips from ipPools: %s for ip used' % str(ip) )
            _path = path + "/" + ip
            self.zk.delete(_path)




   
            
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
            self.zk.delete(port_path)
#             if not nc_ip_port_available(host_ip, port):
#                 assign_port_list.append(port)
            assign_port_list.append(port)
            if len(assign_port_list) == port_count:
                break
        return assign_port_list

    def write_port_into_portPool(self, host_ip, port):
        clusterUUID = self.getClusterUUID()
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
        
        
        
        
        
    '''
    *********************************************Base method*******************************************
    '''
            
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
    
    def getClusterUUID(self):
        logging.debug(self.rootPath)
        dataNodeName = self.zk.get_children(self.rootPath)
        logging.debug(dataNodeName)
        return dataNodeName[0]
    
    def existCluster(self):
        self.zk.ensure_path(self.rootPath)
        clusters = self.zk.get_children(self.rootPath)
        if len(clusters) != 0:
            return True
        return False
    

    
    
    '''
    @todo: move this method to containerOpers or containerClusterOpers?
    '''
    def write_container_status_by_containerName(self, container_name, record):
        containerClusterName = get_containerClusterName_from_containerName(container_name)
        container_ip = self.get_containerIp(containerClusterName, container_name)
        self.__write_container_status(containerClusterName, container_ip, record)
    
    
    
    '''
    @todo: why put this logic to zkOpers?
    '''
    def get_containerName(self, cluster, container_ip):
        container_info = self.retrieve_container_node_value(cluster, container_ip)
        inspect = container_info.get('inspect')
        con = Container(inspect=inspect)
        return con.name()

    '''
    @todo: why put this logic to zkOpers?
    '''
    def get_hostIp(self, cluster, container_ip):
        container_info = self.retrieve_container_node_value(cluster, container_ip)
        return container_info.get('hostIp')
  
