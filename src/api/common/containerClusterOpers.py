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
import copy

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
        
        failed_rst = {'code':"000001"}
        succ_rst = {'code':"000000"}
        check_rst_dict, message_list  = {}, []
        container_count = self.zkOper.retrieve_container_num(container_cluster_name)
        container_node_list = self.zkOper.retrieve_container_list(container_cluster_name)
        
        container_cluster_info = self.zkOper.retrieve_container_cluster_info(container_cluster_name)
        start_flag = container_cluster_info.get('start_flag')
        if not start_flag:
            return failed_rst
            
        if len(container_node_list) != container_count:
            return failed_rst
        
        for container_node in container_node_list:
            container_node_value = self.zkOper.retrieve_container_node_value(container_cluster_name, container_node)
            if not container_node_value:
                return failed_rst
            containerName = container_node_value.get('containerName')
            hostIp = container_node_value.get('hostIp')
            message_list.append(container_node_value)
            
        check_rst_dict.update(succ_rst)
        check_rst_dict.setdefault('containers', message_list)
        check_rst_dict.setdefault('message', 'check all containers OK!')
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
            print ('code exception!')
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
        logging.info('choose host iplist: %s' % str(create_container_node_ip_list) )
        
        container_finished_flag_dict = self.__dispatch_create_container_task(create_container_node_ip_list, create_container_arg_list, 
                                                                             adminUser, adminPasswd)
        logging.info('create container result: %s' % str(container_finished_flag_dict))
        
        check_result = self.__check_result(containerCount, container_finished_flag_dict)
        if check_result:
            self._send_email("container", " container create operation finished on server cluster")
        
        flag = self._check_mlcuster_manager_stat(create_container_node_ip_list, create_container_arg_list, 10)
        
        if flag:
            container_cluster_info = self.zkOper.retrieve_container_cluster_info(containerClusterName)
            container_cluster_info.setdefault('start_flag', 'done')
            self.zkOper.write_container_cluster_info(container_cluster_info)     
    
    
    def _check_mlcuster_manager_stat(self, create_container_node_ip_list, create_container_arg_list, num):
        
        while num:
            result = self.__start_mcluster_manager( create_container_node_ip_list, create_container_arg_list)
            if result:
                logging.info('successful!!!')
                return True
            num -= 1
        
            
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
        args_dict.setdefault('host_ip', host_ip)
        
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
                    env.setdefault('ZKID', i+1)
            
            gateway = self.__get_gateway_from_ip(containerIp)
            env.setdefault('NETMASK', '255.255.255.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'letv_mcluster_docker_db_node_%s' % str(i+1))
            env.setdefault('IP', containerIPList[i])
            
            create_container_arg_dict.setdefault('env', env)
            create_container_arg_list.append(create_container_arg_dict)
        return create_container_arg_list
    
    def __choose_host(self):
        
        create_container_node_ip_list = []
        data_node_info_list = self.zkOper.retrieve_data_node_list()
        if len(data_node_info_list) < 4:
            create_container_node_ip_list = data_node_info_list
            create_container_node_ip_list.append(data_node_info_list[-1])
        
        elif len(data_node_info_list) == 4:
            create_container_node_ip_list = data_node_info_list
        
        else:
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
    
    
    def __get_gateway_from_ip(self, ip):
        ip_item_list = ip.split('.')
        ip_item_list[-1] = '1'
        ip_item_list[-2] = '0'
        return '.'.join(ip_item_list)
    
    def _sort_server_resource(self, dict):
        resource_list = []
        create_node_ip_list = []
        
        for (data_node_ip, resource_sub_dict) in dict.items():
            memoryCount = resource_sub_dict.get('memoryCount')
            
            diskCount = resource_sub_dict.get('diskCount')
            
            resourceCount = memoryCount * 600 + diskCount *0.4
            
            resource_list.append(resourceCount)
            
        resource_list.sort()
        
        for resourceCount in resource_list:
            for (data_node_ip, resource_sub_dict) in dict.items():
                memoryCount = resource_sub_dict.get('memoryCount')
                diskCount = resource_sub_dict.get('diskCount')
                resourceCount_cal_tmp = memoryCount * 600 + diskCount *0.4
                if resourceCount_cal_tmp == resourceCount:
                    create_node_ip_list.insert(0,data_node_ip)
                    del dict[data_node_ip]
                    break
                    
        return create_node_ip_list

    def __start_mcluster_manager(self, create_container_node_ip_list, create_container_arg_list):
        stat = True
        for index,host_ip in enumerate(create_container_node_ip_list):
            containerName = create_container_arg_list[index].get('container_name')
            ret = self.__get(containerName, host_ip)
            if not ret:
                stat = False
        return stat
    
    def __get(self, containerName, container_node):
        args_dict = {}
        
        url_post = "/inner/MclusterManager/status/%s" % containerName
        requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
        logging.info('requesturi: %s' % requesturi)
        
        request = HTTPRequest(url=requesturi, method='GET')
        fetch_ret = _request_fetch(request)
        logging.info('fetch_ret:%s' % str(fetch_ret))
        fetch_ret = json.loads(fetch_ret)
        logging.info('fetch_ret2:%s' % str(fetch_ret))
        logging.info('get type :%s' % str(type(fetch_ret) ) )
        ret = fetch_ret.get('response').get('message')
        logging.info('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
        logging.info('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
        
        return ret
    
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