'''
Created on Sep 8, 2014

@author: root
'''
import sys
import logging
import time
import urllib
import json

from tornado.options import options
from api.common.abstractAsyncThread import Abstract_Async_Thread
from api.common.abstractContainerOpers import Abstract_Container_Opers
from tornado.httpclient import HTTPRequest
from api.common.helper import _retrieve_userName_passwd
from api.common.helper import _request_fetch

class ContainerCluster_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
        
    def create(self, dict):
        containerCluster_create_action = ContainerCluster_Create_Action(dict)
        containerCluster_create_action.start()
        
    def destory(self):
        pass

class ContainerCluster_Create_Action(Abstract_Async_Thread):
    
    dict = {}
    
    def __init__(self, dict):
        super(ContainerCluster_Create_Action, self).__init__()
        self.dict = dict
        
    def run(self):
        try:
            self._issue_create_action(self.dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
            
    def _issue_create_action(self, dict):
        containerCount_txt = dict.get('containerCount')
        containerCount = int(containerCount_txt)
        
        containerName = dict.get('containerName')
        
        container_finished_flag_dict = {}
        data_node_info_list = self.zkOper.retrieve_data_node_list()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        
        url_post = "/server"
        resource_dict = {}
        for data_node_ip in data_node_info_list:
            requesturi = "http://%s:%s%s" % (data_node_ip, options.port, url_post)
            request = HTTPRequest(url=requesturi, method='GET')
            return_result = _request_fetch(request)
            retrun_dict = json.loads(return_result)
            resource_dict.setdefault(data_node_ip, retrun_dict['response'])
            
        logging.info("Before sort, all server the resource info, the resource value is %s" % str(resource_dict))
            
        create_container_node_ip_list = self._sort_server_resource(resource_dict)
        
        logging.info("After sort, the resource list is %s" % str(create_container_node_ip_list))
        
        containerIPList = self.retrieve_ip_resource(containerCount)
        
        self.create_container_cluser_info(containerCount, containerName)
        
        dict.setdefault('container_type', 'mclusternode')
        for i in range(3):
            container_ip = dict.setdefault('containerIp', containerIPList[i])
            data_node_ip = create_container_node_ip_list[i]
            create_finished = self.issue_create_container_request(data_node_ip, container_ip, dict, adminUser, adminPasswd)
            container_finished_flag_dict.setdefault(data_node_ip, create_finished)
            
        dict.setdefault('container_type', 'mclustervip')
        dict.setdefault('containerIp', containerIPList[3])
        data_node_ip = create_container_node_ip_list[3]
        create_finished = self.issue_create_container_request(data_node_ip, container_ip, dict, adminUser, adminPasswd)
        container_finished_flag_dict.setdefault(data_node_ip, create_finished)
            
        container_create_finished_count = 0
        for data_node_ip, create_finished in container_finished_flag_dict.iteritems():
            if create_finished:
                container_create_finished_count += 1
                
        if container_create_finished_count == containerCount:
            self._send_email("container", " container create operation finished on server cluster")
            
            
            
            
    def retrieve_ip_resource(self, createContainerCount):
        containerIPList = None
        
        isLock,lock = self.zkOper.lock_assign_ip()
        try:
            if isLock:
                containerIPList = self.zkOper.retrieve_ip(createContainerCount)
        finally:
            if isLock:
                self.zkOper.unLock_assign_ip(lock)
                
        return containerIPList
    
    def create_container_cluser_info(self, containerCount, containerClusterName):
        containerClusterProps = {}
        containerClusterProps.setdefault('containerCount', containerCount)
        containerClusterProps.setdefault('containerClusterName', containerClusterName)
        self.zkOper.write_container_cluster_info(containerClusterProps)
            
            
    def issue_create_container_request(self, data_node_ip, container_ip, args_dict, adminUser, adminPasswd):
        args_dict.setdefault("containerIp", container_ip)
        url_post = "/inner/container"
        requesturi = "http://%s:%s%s" % (data_node_ip, options.port, url_post)
        request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args_dict), \
                              auth_username = adminUser, auth_password = adminPasswd)
            
        _request_fetch(request)
            
        create_finished = self._check_create_status(container_ip)
        
        return create_finished
        
        
        
    def _sort_server_resource(self, dict):
        resource_list = []
        create_node_ip_list = []
        
        for (data_node_ip, resource_sub_dict) in dict.items():
            memoryCount = resource_sub_dict.get('memoryCount')
            
            diskCount = resource_sub_dict.get('diskCount')
            
            resourceCount = memoryCount * 0.4 + diskCount *0.6
            
            resource_list.append(resourceCount)
            
        resource_list.sort()
        
        for resourceCount in resource_list:
            for (data_node_ip, resource_sub_dict) in dict.items():
                memoryCount = resource_sub_dict.get('memoryCount')
            
                diskCount = resource_sub_dict.get('diskCount')
            
                resourceCount_cal_tmp = memoryCount * 0.4 + diskCount *0.6
                
                if resourceCount_cal_tmp == resourceCount:
                    create_node_ip_list.insert(0,data_node_ip)
                    del dict[data_node_ip]
                    break
                    
        return create_node_ip_list
                    
    
    def _check_create_status(self, container_ip):
        
        create_finished = False
        
        while not create_finished:
            
            created_nodes = self.zkOper.retrieve_started_nodes()
            
            for i in range(len(created_nodes)):
                started_node = created_nodes[i]
                if started_node == container_ip:
                    create_finished = True
                    
            time.sleep(1)
            
        return create_finished