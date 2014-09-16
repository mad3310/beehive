'''
Created on Sep 8, 2014

@author: root
'''
import sys
import logging
import time
import urllib
import json
import traceback

from tornado.httpclient import HTTPRequest
from tornado.options import options
from common.abstractAsyncThread import Abstract_Async_Thread
from common.abstractContainerOpers import Abstract_Container_Opers
from common.helper import _request_fetch, _retrieve_userName_passwd

class ContainerCluster_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, dict):
        logging.info('create msg: %s' % dict)
        containerCluster_create_action = ContainerCluster_Create_Action(dict)
        containerCluster_create_action.start()
    
    def check(self, container_cluster_name):
        check_rst_dict, message_list  = {}, []
        container_count = self.zkOper.retrieve_container_num(container_cluster_name)
        container_node_list = self.zkOper.retrieve_container_list(container_cluster_name)
        if len(container_node_list) != container_count:
            check_rst_dict.setdefault('code', "000001")
        else:
            for container_node in container_node_list:
                container_node_value = self.zkOper.retrieve_container_node_value(container_cluster_name, container_node)
                check_rst_dict.setdefault('code', "000000")
                message_list.append(container_node_value)
            check_rst_dict.setdefault('message', message_list)
        return check_rst_dict
    
    def destory(self):
        pass

class ContainerCluster_Create_Action(Abstract_Async_Thread):    
    dict = {}
    
    def __init__(self, dict):
        super(ContainerCluster_Create_Action, self).__init__()
        self.dict = dict
        
    def run(self):
        try:
            logging.info('begin create')
            self._issue_create_action(self.dict)
        except:
            logging.info(traceback.format_exc())
            self.threading_exception_queue.put(sys.exc_info())
       
    def _issue_create_action(self, args={}):
        
        logging.info('args:%s' % str(args))
        containerClusterName = args.get('containerClusterName')
        logging.info('containerClusterName : %s' % str(containerClusterName))
        containerCount = 4
        self.create_container_cluser_info(containerCount, containerClusterName)
        adminUser, adminPasswd = _retrieve_userName_passwd()
        
        create_container_arg_list = self.__get_container_params(containerCount, containerClusterName)
        
        create_container_node_ip_list = self.__choose_host()
        
        container_finished_flag_dict = self.__dispatch_create_container_task(create_container_node_ip_list, create_container_arg_list, 
                                                                             adminUser, adminPasswd)
        logging.info('create container result: %s' % str(container_finished_flag_dict))
        
        check_result = self.__check_result(containerCount, container_finished_flag_dict)
        if check_result:
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
     
    def issue_create_container_request(self, host_ip,  args_dict, adminUser, adminPasswd):
        url_post = "/inner/container" 
        requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
        logging.info('requesturi:%s' % requesturi)
        logging.info('args_dict:%s' % args_dict)
        
        request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args_dict), \
                              auth_username = adminUser, auth_password = adminPasswd)
        
        _request_fetch(request)

        return True
    
    def __get_container_params(self, containerCount, containerClusterName):

        create_container_arg_list = []
        containerIPList = self.retrieve_ip_resource(containerCount)
        
        for i in range(int(containerCount)):
            create_container_arg_dict, env = {}, {}
            create_container_arg_dict.setdefault('containerClusterName', containerClusterName)
            create_container_arg_dict['container_ip'] = containerIPList[i]
            create_container_arg_dict['container_name'] = 'd_mcl_%s_node_%s' % (containerClusterName, str(i+1))
            #create_container_arg_dict.setdefault('volumes', ['/srv/mcluster', '/data/mcluster_data'])
            create_container_arg_dict.setdefault('volumes', ['/data/mcluster_data'])
            
            if i == int(containerCount-1):
                create_container_arg_dict['container_type'] = 'mclustervip'
                
            else:
                create_container_arg_dict['container_type'] = 'mclusternode'
                for j, containerIp in enumerate(containerIPList):
                    num = j+1
                    env.setdefault('N%s_IP' % str(num), containerIp)
                    env.setdefault('N%d_HOSTNAME' % num, 'letv_mcluster_docker_db_node_%d' % num)
            
            env.setdefault('NETMASK', '255.255.255.0')
            env.setdefault('GATEWAY', '10.200.85.1')
            env.setdefault('ZKID', i+1)
            env.setdefault('HOSTNAME', 'letv_mcluster_docker_db_node_%s' % str(i+1))
            env.setdefault('IP', containerIPList[i])
            
            create_container_arg_dict.setdefault('env', env)
            create_container_arg_list.append(create_container_arg_dict)
            
        return create_container_arg_list
    
    def __choose_host(self):
        
        data_node_info_list = self.zkOper.retrieve_data_node_list()
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
        
        return create_container_node_ip_list
        
    def __dispatch_create_container_task(self, create_container_node_ip_list,  create_container_arg_list, adminUser, adminPasswd):
        container_finished_flag_dict = {}
        for i in range(4):
            args_dict = create_container_arg_list[i]
            host_ip = create_container_node_ip_list[i]
            create_finished = self.issue_create_container_request(host_ip,  args_dict, adminUser, adminPasswd)
            container_finished_flag_dict.setdefault(host_ip, create_finished)
        return container_finished_flag_dict
            
    def __check_result(self, containerCount, container_finished_flag_dict):
        container_create_finished_count = 0
        for data_node_ip, create_finished in container_finished_flag_dict.iteritems():
            if create_finished:
                container_create_finished_count += 1
        return container_create_finished_count == containerCount
    
    def __check_create_status(self, container_ip):
        
        create_finished = False
        
        while not create_finished:
            
            created_nodes = self.zkOper.retrieve_started_nodes()
            
            for i in range(len(created_nodes)):
                started_node = created_nodes[i]
                if started_node == container_ip:
                    create_finished = True
            time.sleep(1)
        return create_finished