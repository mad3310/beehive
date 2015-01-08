#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: root
'''
import sys, time, copy, random, re
import logging, traceback

from tornado.options import options
from abstractAsyncThread import Abstract_Async_Thread
from abstractContainerOpers import Abstract_Container_Opers
from helper import _request_fetch, _retrieve_userName_passwd
from utils.exceptions import MyError
from utils.autoutil import *
from zkOpers import ZkOpers
from resourceVerify import ResourceVerify
from container_module import Container
from utils.threading_exception_queue import Threading_Exception_Queue


class ContainerCluster_Opers(Abstract_Container_Opers):
        
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, dict):
        logging.info('create msg: %s' % dict)
        containerCluster_create_action = ContainerCluster_Create_Action(dict)
        containerCluster_create_action.start()
    
    def start(self, containerClusterName):
        containerCluster_start_action = ContainerCluster_start_Action(containerClusterName)
        containerCluster_start_action.start()
        
    def stop(self, containerClusterName):
        containerCluster_stop_action = ContainerCluster_stop_Action(containerClusterName)
        containerCluster_stop_action.start()

    def destory(self, containerClusterName):
        containerCluster_destroy_action = ContainerCluster_destroy_Action(containerClusterName)
        containerCluster_destroy_action.start()
   
    def check(self, containerClusterName):
        try:
            nodes_status, cluster_status = [], {}
            normal, vip, nodes_stat = [], [], {}
            container_ip_list = self.zkOper.retrieve_container_list(containerClusterName)
            for container_ip in container_ip_list:
                status = self.zkOper.retrieve_container_status_value(containerClusterName, container_ip)
                logging.info('get container status dict: %s' % str(status) )
                con_info = self.zkOper.retrieve_container_node_value(containerClusterName, container_ip)
                node_type = con_info.get('type')
                if node_type == 'mclusternode':
                    normal.append(status.get('status'))
                    nodes_stat.setdefault('normal', normal)
                elif node_type == 'mclustervip':
                    vip.append(status.get('status'))
                    nodes_stat.setdefault('vip', vip)
            
            ret = self._get_cluster_status(nodes_stat)
            cluster_status.setdefault('status', ret)
            
            if ret == 'destroyed':
                logging.info('delete containerCluster: %s' % containerClusterName)
                self.zkOper.delete_container_cluster(containerClusterName)
            
            return cluster_status
        except:
            logging.error(str( traceback.format_exc()) )
    
    def _get_cluster_status(self, nodes_stat):
        
        stat_set = ['starting', 'started', 'stopping', 'stopped', 'destroying', 'destroyed']
        normal_nodes_stat, all_nodes_stat = [], []
        if not isinstance(nodes_stat, dict):
            cluster_stat = 'failed'
        vip = nodes_stat.get('vip')
        normal = nodes_stat.get('normal')
        if vip:
            vip_node = vip[0]
            logging.info('vip:%s' % str(vip_node))
            all_nodes_stat.append(vip_node)
        if normal:
            for normal_node in normal:
                normal_nodes_stat.append(normal_node)
                all_nodes_stat.append(normal_node)

        stat_set_list = list(set(all_nodes_stat))
        if len(stat_set_list) == 1:
            stat = stat_set_list[0]
            if stat_set_list[0] in stat_set:
                cluster_stat = stat
            else:
                cluster_stat = 'failed'
        else:
            i = 0
            for normal_node in normal_nodes_stat:
                if normal_node == 'started':
                    i += 1
            if i == 2:
                cluster_stat = 'danger'
            elif i ==1:
                cluster_stat = 'crisis'
            else:
                cluster_stat = 'failed'
        return cluster_stat

    def __get_create_info(self, containerClusterName, container_node):
        create_info = {}
        container_node_value = self.zkOper.retrieve_container_node_value(containerClusterName, container_node)
        con = Container()
        create_info = con.create_info(container_node_value)
        return create_info

#     def __get_create_info(self, containerClusterName, container_node):
#         create_info = {}
#         container_node_value = self.zkOper.retrieve_container_node_value(containerClusterName, container_node)
#         inspect = container_node_value.get('inspect')
#         
#         create_info.setdefault('hostIp', container_node_value.get('hostIp') )
#         create_info.setdefault('type', container_node_value.get('type') )
#         con = Container(inspect=inspect)
#         container_name = con.name()
#         create_info.setdefault('containerClusterName', con.cluster(container_name) )
#         create_info.setdefault('zookeeperId', con.zookeeper_id() )
#         create_info.setdefault('gateAddr', con.gateway() )
#         create_info.setdefault('netMask', con.netmask() )
#         create_info.setdefault('mountDir', str(con.volumes()) )
#         create_info.setdefault('ipAddr', con.ip() )
#         create_info.setdefault('containerName', con.name() )
#         return create_info

    def check_create_status(self, containerClusterName):
        failed_rst = {'code':"000001"}
        succ_rst = {'code':"000000"}
        lack_rst = {'code':"000002"}
        check_rst_dict, message_list  = {}, []
        container_count = self.zkOper.retrieve_container_num(containerClusterName)
        container_node_list = self.zkOper.retrieve_container_list(containerClusterName)
        
        container_cluster_info = self.zkOper.retrieve_container_cluster_info(containerClusterName)
        start_flag = container_cluster_info.get('start_flag')

        if not start_flag:
            return failed_rst
        else:
            if start_flag == 'succeed':
                for container_node in container_node_list:
                    container_node_value = self.__get_create_info(containerClusterName, container_node)
                    message_list.append(container_node_value)
                check_rst_dict.update(succ_rst)
                check_rst_dict.setdefault('containers', message_list)
                check_rst_dict.setdefault('message', 'check all containers OK!')
            
            elif  start_flag == 'lack_resource':
                check_rst_dict.update(lack_rst)
                check_rst_dict.setdefault('error_msg', container_cluster_info.get('error_msg'))
                logging.info('return info:%s' % str(check_rst_dict))
            
            elif start_flag == 'failed':
                check_rst_dict.update(lack_rst)
                check_rst_dict.setdefault('error_msg', 'check mcluster stat failed')            
            
            return check_rst_dict

    def __rewrite_config(self, conf_dict):
        check_mcluster = conf_dict.get('check_mcluster')
        if check_mcluster:
            conf_dict['check_mcluster'] = bool(check_mcluster)
        
        is_res_verify = conf_dict.get('is_res_verify')
        if is_res_verify:
            conf_dict['is_res_verify'] = bool(is_res_verify)
        
        mem_free_limit = conf_dict.get('mem_free_limit')
        if mem_free_limit:
            conf_dict['mem_free_limit'] = int(mem_free_limit)

        nodeCount = conf_dict.get('nodeCount')
        if nodeCount:
            conf_dict['nodeCount'] = int(nodeCount)
        return conf_dict
  
    def config(self, conf_dict={}):
        
        try:
            error_msg = ''
            logging.info('config args: %s' % conf_dict)
            if 'type' in conf_dict:
                _type = conf_dict.pop('type')
                if _type == 'normal':
                    conf_record = self.zkOper.retrieve_mcluster_info_from_config()
                    re_conf_dict = self.__rewrite_conf_info(conf_dict, conf_record)
                    self.zkOper.writeClusterNormalConf(re_conf_dict)
                elif _type == 'vip':
                    conf_record = self.zkOper.retrieve_mclustervip_info_from_config()
                    re_conf_dict = self.__rewrite_conf_info(conf_dict, conf_record)
                    self.zkOper.writeClusterVipConf(re_conf_dict)
            elif 'servers' in conf_dict:
                error_msg = self.__update_white_list(conf_dict)
            elif 'nodeCount' in conf_dict:
                conf_dict = self.__rewrite_config(conf_dict)
                self.zkOper.writeConfigVerify(conf_dict)
            else:
                error_msg = 'the key of the params is not correct'
        except:
            error_msg = str( traceback.format_exc() )
            logging.error( error_msg )
        finally:
            return error_msg
    
    def __update_white_list(self, conf_dict):
        error_msg = ''
        conf_white_str = conf_dict.get('servers')
        ip_pattern = '(((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?),)+((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)'
        if not re.match(ip_pattern, conf_white_str):
            error_msg = 'the values of the params is not correct'
            logging.error(error_msg)
            return error_msg
        conf_white_list = conf_white_str.split(',')
        privs_white_list = self.zkOper.retrieve_servers_white_list()
        add = list( set(conf_white_list) - set(privs_white_list) )
        delete = list( set(privs_white_list) - set(conf_white_list) )
        both = list( set(privs_white_list) & set(conf_white_list) )
        for item in add:
            self.zkOper.add_server_into_white_list(item)
        for item in delete:
            self.zkOper.del_server_from_white_list(item)
        return error_msg      
            
    def __rewrite_conf_info(self, conf_dict, conf_record):
        for key, value in conf_dict.items():
            if key == 'mem_limit':
                value = eval(value)
            if key in conf_record:
                conf_record[key] = value
            else:
                conf_record.setdefault(key, value)
        return conf_record


class ContainerCluster_Action(Abstract_Async_Thread):
    
    def __init__(self, containerClusterName, action):
        super(ContainerCluster_Action, self).__init__()
        self.cluster = containerClusterName
        self.action = action
        
    def run(self):
        try:
            logging.info('do cluster %s ' % self.action)
            self._issue_action()
        except:
            logging.error( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())
    
    def _issue_action(self):
        params = self.get_params()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        self.dispatch_container_tasks(params, adminUser, adminPasswd)
   
    def dispatch_container_tasks(self, params, admin_user, admin_passwd):
        logging.info('params: %s' % str(params))
        for host_ip, container_name in params.items():
            if isinstance(container_name, str) or isinstance(container_name, unicode):
                self.post(host_ip, container_name, admin_user, admin_passwd)
            elif isinstance(container_name, list):
                logging.info('container_name_list : %s' % str(container_name))
                for _name in container_name:
                    self.post(host_ip, _name, admin_user, admin_passwd)
        
        if self.action == 'remove':
            container_ip_list = self.zkOper.retrieve_container_list(self.cluster)
            logging.info('container_ip_list:%s' % str(container_ip_list) )
            self.zkOper.recover_ips_to_pool(container_ip_list)
          
    def post(self, host_ip, container_name, admin_user, admin_passwd):
        args = {}
        args.setdefault('containerName', container_name)
        request_uri = 'http://%s:%s/container/%s' % (host_ip, options.port, self.action)
        logging.info('post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
        ret = http_post(request_uri, args, auth_username = admin_user, auth_password = admin_passwd)
        logging.info('result: %s' % str(ret))
    
    def get_params(self):
        """
            two containers may be with a host_ip
        """
        
        params, container_info = {}, {}
        
        container_ip_list = self.zkOper.retrieve_container_list(self.cluster)
        
        for contaier_ip in container_ip_list:
            container_name_list = []
            container_info = self.zkOper.retrieve_container_node_value(self.cluster, contaier_ip)
            container_name = container_info.get('containerName')
            host_ip = container_info.get('hostIp')
            if host_ip in params:
                container_name_list.append(params[host_ip])
                container_name_list.append(container_name)
                params[host_ip] = container_name_list
            else:
                params.setdefault(host_ip, container_name)
        return params
     

class ContainerCluster_stop_Action(ContainerCluster_Action):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_stop_Action, self).__init__(containerClusterName, 'stop')


class ContainerCluster_start_Action(ContainerCluster_Action):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_start_Action, self).__init__(containerClusterName, 'start')
        

class ContainerCluster_destroy_Action(ContainerCluster_Action):
    
    def __init__(self, containerClusterName):
        super(ContainerCluster_destroy_Action, self).__init__(containerClusterName, 'remove')


class ContainerCluster_Create_Action(Abstract_Async_Thread): 
    _dict = {}
    
    def __init__(self, _dict):
        super(ContainerCluster_Create_Action, self).__init__()
        self.dict = _dict
        
    def run(self):
        try:
            logging.info('begin create')
            self._issue_create_action(self.dict)
        except:
            logging.info( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())
  
    def _issue_create_action(self, args={}):
        logging.info('args:%s' % str(args))
        containerClusterName = args.get('containerClusterName')
        logging.info('containerClusterName : %s' % str(containerClusterName))
        
        verify_item = self.zkOper.retrieve_config_node_value()
        logging.info('config node info in zk: %s, type: %s' % ( str( verify_item), type(verify_item)) )
        
        select_ip_list = []
        is_res_verify = verify_item.get('is_res_verify')
        if is_res_verify:
            res_verify = ResourceVerify(verify_item)
            ret = res_verify.check_resource()
            error_msg = ret.get('error_msg')
            if error_msg:
                container_cluster_info = {}
                container_cluster_info['containerClusterName'] = containerClusterName
                container_cluster_info['start_flag'] = 'lack_resource'
                container_cluster_info['error_msg'] = error_msg
                self.zkOper.write_container_cluster_info(container_cluster_info)
                logging.info('check resource failed:%s' % str(error_msg) )
                return
            else:
                select_ip_list = ret.get('select_ip_list')
                logging.info('select_ip_list:%s' % str(select_ip_list))
        
        containerCount = verify_item.get('nodeCount')
        self.create_container_cluser_info(containerCount, containerClusterName)
        adminUser, adminPasswd = _retrieve_userName_passwd()
        
        create_container_arg_list = self._get_container_params(containerCount, containerClusterName, adminUser, adminPasswd)

        if select_ip_list:
            create_container_node_ip_list = select_ip_list
        else:
            create_container_node_ip_list = self.__choose_host()
        
        logging.info('choose host iplist: %s' % str(create_container_node_ip_list) )
        
        container_finished_flag_dict = self.__dispatch_create_container_task(create_container_node_ip_list, create_container_arg_list, 
                                                                             containerCount, adminUser, adminPasswd)
        logging.info('create container result: %s' % str(container_finished_flag_dict))
                      
        check_result = self.__check_result(create_container_node_ip_list, container_finished_flag_dict)
        logging.info('check_result: %s' % check_result)
        if not check_result:
            raise MyError('not all container succeed created')
        
        flag = True
        check_mcluster = verify_item.get('check_mcluster')
        if check_mcluster:
            flag = self._check_mcluster_manager_stat(create_container_node_ip_list, create_container_arg_list, 6)
        if flag:
            container_cluster_info = self.zkOper.retrieve_container_cluster_info(containerClusterName)
            container_cluster_info.setdefault('start_flag', 'succeed')
            self.zkOper.write_container_cluster_info(container_cluster_info)
        else:
            container_cluster_info = self.zkOper.retrieve_container_cluster_info(containerClusterName)
            container_cluster_info['start_flag'] = 'failed'
            self.zkOper.write_container_cluster_info(container_cluster_info)
            logging.info('check mlcuster manager stat failed :%s' % containerClusterName)
        
    def __retrieve_ip_resource(self, createContainerCount):
        containerIPList = None
        isLock,lock = self.zkOper.lock_assign_ip()
        try:
            if isLock:
                containerIPList = self.zkOper.retrieve_ip(createContainerCount)
        except:
            logging.error( str(traceback.format_exc() ) )
        finally:
            if isLock:
                self.zkOper.unLock_assign_ip(lock)
        return containerIPList
    
    def create_container_cluser_info(self, containerCount, containerClusterName):
        containerClusterProps = {}
        containerClusterProps.setdefault('containerCount', containerCount)
        containerClusterProps.setdefault('containerClusterName', containerClusterName)
        self.zkOper.write_container_cluster_info(containerClusterProps)
     
    def issue_create_container_request(self, host_ip,  args_dict, admin_user, admin_passwd):
        url_post = "/inner/container" 
        requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
        logging.info('requesturi:%s' % requesturi)
        logging.info('args_dict:%s' % args_dict)
        args_dict.setdefault('host_ip', host_ip)
        try:
            fetch_ret = http_post(requesturi, args_dict, _connect_timeout=100.0, _request_timeout=100.0, \
                                  auth_username=admin_user, auth_password=admin_passwd )
            logging.info('POST result :%s' % str(fetch_ret))
            if not isinstance(fetch_ret, dict):
                logging.error('create container in server : %s failed or code exception! please check' % host_ip)
                return False
            ret = fetch_ret.get('response').get('message')
            if ret == 'Success Create Container':
                return True
        except:
            logging.error(str(traceback.format_exc()))
            return False

    def _get_container_params(self, containerCount, containerClusterName, adminUser, adminPasswd):
        
        create_container_arg_list = []
        containerIPList = self.__retrieve_ip_resource(containerCount)
        volumes, binds = self.__get_normal_volumes_args()
        for i in range(int(containerCount)):
            create_container_arg, env = {}, {}
            create_container_arg.setdefault('containerClusterName', containerClusterName)
            create_container_arg['container_ip'] = containerIPList[i]
            container_name = 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1))
            create_container_arg['container_name'] = container_name
                        
            if i == int(containerCount-1):
                create_container_arg['container_type'] = 'mclustervip'
            else:
                create_container_arg['container_type'] = 'mclusternode'
                create_container_arg.setdefault('volumes', volumes)
                create_container_arg.setdefault('binds', binds)
                for j, containerIp in enumerate(containerIPList[:3]):
                    env.setdefault('N%s_IP' % str(j+1), containerIp)
                    env.setdefault('N%s_HOSTNAME' % str(j+1), 'd-mcl-%s-n-%s' % (containerClusterName, str(j+1)))
                    env.setdefault('ZKID', i+1)
            
            gateway = self.__get_gateway_from_ip(containerIp)
            env.setdefault('NETMASK', '255.255.0.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd-mcl-%s-n-%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', containerIPList[i])
            
            create_container_arg.setdefault('env', env)
            create_container_arg_list.append(create_container_arg)
        return create_container_arg_list
    
    def __get_normal_volumes_args(self):
        volumes, binds = {}, {}
        mcluster_conf_info = self.zkOper.retrieve_mcluster_info_from_config()
        logging.info('mcluster_conf_info: %s' % str(mcluster_conf_info))
        mount_dir = eval( mcluster_conf_info.get('mountDir') )
        for k,v in mount_dir.items():
            volumes.setdefault(k, v)
            if '/srv/mcluster' in k:
                binds = {}
            else:
                binds.setdefault(v, {'bind': k})
        return volumes, binds
    
    def __choose_host(self):
        
        create_container_node_ip_list = []
        data_node_info_list = self.zkOper.retrieve_data_node_list()
        data_node_info_list.sort()
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
                return_dict = http_get(requesturi)
                resource_dict.setdefault(data_node_ip, return_dict['response'])
            logging.info("Before sort, all server the resource info, the resource value is %s" % str(resource_dict))
            create_container_node_ip_list = self._sort_server_resource(resource_dict)
            logging.info("After sort, the resource list is %s" % str(create_container_node_ip_list))
        return create_container_node_ip_list
        
    def __dispatch_create_container_task(self, create_container_node_ip_list,  create_container_arg_list, 
                                         container_count, admin_user, admin_passwd):
        #logging.info('create_container_arg_list :%s' % str(create_container_arg_list))
        container_finished_flag_dict = {}
        for i in range(container_count):
            args_dict = create_container_arg_list[i]
            host_ip = create_container_node_ip_list[i]
            container_name = args_dict.get('container_name')
            container_ip = args_dict.get('container_ip')
            create_finished = self.issue_create_container_request(host_ip,  args_dict, admin_user, admin_passwd)
            container_finished_flag_dict.setdefault(host_ip, create_finished)
        return container_finished_flag_dict
            
    def __check_result(self, create_container_node_ip_list, container_finished_flag_dict):
        host_ip_list = list(set(create_container_node_ip_list))
        containerCount = len(host_ip_list)
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
            resourceCount = memoryCount * 0.6 + diskCount *0.4
            resource_list.append(resourceCount)
        resource_list.sort()
        for resourceCount in resource_list:
            for (data_node_ip, resource_sub_dict) in dict.items():
                memoryCount = resource_sub_dict.get('memoryCount')
                diskCount = resource_sub_dict.get('diskCount')
                resourceCount_cal_tmp = memoryCount * 0.6 + diskCount *0.4
                if resourceCount_cal_tmp == resourceCount:
                    create_node_ip_list.insert(0,data_node_ip)
                    del dict[data_node_ip]
                    break
        return create_node_ip_list
    
    def _check_mcluster_manager_stat(self, create_container_node_ip_list, create_container_arg_list, num):
        container_name_list = []
        check_container_node_ip_list = []
        for index, create_container_arg in enumerate(create_container_arg_list):
            if create_container_arg.get('container_type') == 'mclusternode':
                container_name_list.append(create_container_arg.get('container_name'))
                check_container_node_ip_list.append(create_container_node_ip_list[index])
        #container_name_list = self.__get_containerName_list(create_container_arg_list)
        logging.info('wait 5 seconds...')
        time.sleep(5)
        while num:
            stat = True
            succ = {}
            logging.info('check_container_node_ip_list :%s' % str(check_container_node_ip_list) )
            for index,host_ip in enumerate(check_container_node_ip_list):
                container_name = container_name_list[index]
                ret = self.__get(container_name, host_ip)
                logging.info('check container %s,  result : %s' % (container_name, str(ret)))
                if ret:
                    succ.setdefault(host_ip, container_name)
                else:
                    stat = False
            logging.info('stat: %s' % str(stat))
            if stat:
                logging.info('successful!!!')
                return True
            
            for hostip, containername in succ.items():
                container_name_list.remove(containername)
                check_container_node_ip_list.remove(hostip)
            num -= 1
    
    def __get_containerName_list(self, create_container_arg_list):
        container_name_list = []
        for create_container_arg in create_container_arg_list:
            container_name = create_container_arg.get('container_name')
            container_name_list.append(container_name)
        return container_name_list
    
    def __get(self, containerName, container_node):
        args_dict = {}
        
        url_post = "/inner/MclusterManager/status/%s" % containerName
        requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
        logging.info('requesturi: %s' % requesturi)
        try:
            fetch_ret = http_get(requesturi)
            logging.info('fetch_ret:%s' % str(fetch_ret))
            ret = fetch_ret.get('response').get('message')
            logging.info('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
            logging.info('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
            return ret
        except:
            return False


class ClusterInfoCollector(Abstract_Container_Opers):
    
    def __init__(self):
        pass
    
    def get_clusters_zk(self):
        clusters_zk_info = {}
        cluster_name_list = self.zkOper.retrieve_cluster_list()
        for cluster_name in cluster_name_list:
            cluster_info_dict = self.get_cluster_zk(cluster_name)
            clusters_zk_info.setdefault(cluster_name, cluster_info_dict)
        return clusters_zk_info
    
    def get_cluster_zk(self, cluster_name):
        cluster_zk_info = {}
        container_ip_list = self.zkOper.retrieve_container_list(cluster_name)
        if len(container_ip_list) != 0:
            for container_ip in container_ip_list:
                container_node = {}
                create_info = self.zkOper.retrieve_container_node_value(cluster_name, container_ip)
                status = self.zkOper.retrieve_container_status_value(cluster_name, container_ip)
                container_node.setdefault('create_info', create_info)
                container_node.setdefault('status', status)
                cluster_zk_info.setdefault(container_ip, container_node)
        return cluster_zk_info


class GetClustersChanges(Abstract_Container_Opers):
    
    def __init__(self):
        pass
    
    def get_res(self):
        host_ip = self.random_host_ip()
        self._get(host_ip, '/serverCluster/update')
        res = self._get(host_ip, '/containerCluster/info')
        logging.info('res : %s' % str(res) )
        return self.__reget_res(res)
    
    def random_host_ip(self):
        host_ip_list = self.zkOper.retrieve_data_node_list()
        host = getHostIp()
        if host in host_ip_list:
            host_ip_list.remove(host)
        host_ip = random.choice(host_ip_list)
        return host_ip
    
    def _get(self, host_ip, url_get):
        try:
            adminUser, adminPasswd = _retrieve_userName_passwd()
            uri = 'http://%s:%s%s' % (host_ip, options.port, url_get)
            logging.info('get uri :%s' % uri)
            ret = http_get(uri, auth_username = adminUser, auth_password = adminPasswd)
            return ret.get('response')
        except:
            logging.error( str(traceback.format_exc()) )

    def __reget_res(self, res):
        
        clusters = []
        for cluster_name, nodes in res.items():
            cluster, nodeInfo = {}, []
            cluster_exist = self.__get_cluster_status(nodes)
            cluster.setdefault('status', cluster_exist)
            cluster.setdefault('clusterName', cluster_name)
            for node_ip,node_value in nodes.items():
                create_info = node_value.get('create_info')
                con = Container()
                create_info = con.create_info(create_info)
                nodeInfo.append(create_info)
            cluster.setdefault('nodeInfo', nodeInfo)
            clusters.append(cluster)
        return clusters
    
    def __get_cluster_status(self, nodes):
        n = 0
        for container_ip,container_info in nodes.items():
            stat = container_info.get('status').get('status')
            if stat == 'destroyed':
                n += 1
        if n == len(nodes):
            exist = 'destroyed'
        else:
            exist = 'alive'
        return exist
