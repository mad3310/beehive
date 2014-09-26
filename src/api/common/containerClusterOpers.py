'''
Created on Sep 8, 2014

@author: root
'''
import sys, time, json, copy, random
import logging, urllib, traceback

from tornado.httpclient import HTTPRequest
from tornado.options import options
from abstractAsyncThread import Abstract_Async_Thread
from abstractContainerOpers import Abstract_Container_Opers
from helper import _request_fetch, _retrieve_userName_passwd
from utils.exceptions import MyError
from utils.autoutil import *


class ContainerCluster_Opers(Abstract_Container_Opers):
    
    def __init__(self):
        super(ContainerCluster_Opers, self).__init__()
    
    def create(self, dict):
        logging.info('create msg: %s' % dict)
        containerCluster_create_action = ContainerCluster_Create_Action(dict)
        containerCluster_create_action.start()

    def destory(self, dict):
        logging.info('destory msg: %s' % dict)
        containerCluster_destory_action = ContainerCluster_destory_Action(dict)
        containerCluster_destory_action.start()
    
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
    
    def config(self, conf_dict={}):
        
        logging.info('config args: %s' % conf_dict)
        _type = conf_dict.pop('type')
        if _type == 'normal':
            conf_record = self.zkOper.retrieve_mcluster_info_from_config()
            re_conf_dict = self.__rewrite_conf_info(conf_dict, conf_record)
            self.zkOper.writeClusterNormalConf(re_conf_dict)
        elif _type == 'vip':
            conf_record = self.zkOper.retrieve_mclustervip_info_from_config()
            re_conf_dict = self.__rewrite_conf_info(conf_dict, conf_record)
            self.zkOper.writeClusterVipConf(re_conf_dict)

    def __rewrite_conf_info(self, conf_dict, conf_record):
        for key, value in conf_dict.items():
            if key in conf_record:
                conf_record[key] = value
            else:
                conf_record.setdefault(key, value)
        return conf_record


class ContainerCluster_destory_Action(Abstract_Async_Thread):
    _dict = {}
    
    def __init__(self, _dict):
        super(ContainerCluster_destory_Action, self).__init__()
        self.dict = _dict
        
    def run(self):
        try:
            logging.info('begin destory')
            self._issue_destory_action(self.dict)
        except:
            print ('code exception!')
            logging.info(traceback.format_exc())
            self.threading_exception_queue.put(sys.exc_info())
    
    def _issue_destory_action(self, args):
        try:
            containerClusterName = args.get('containerClusterName')
            destory_params = self.__get_destory_params(containerClusterName)
            adminUser, adminPasswd = _retrieve_userName_passwd()
            self.__dispatch_destory_container_tasks(destory_params, adminUser, adminPasswd)
        except:
            logging.error(str(traceback.format_exc()))
    
    def __dispatch_destory_container_tasks(self, destory_params, admin_user, admin_passwd):
        logging.info('destory_params: %s' % str(destory_params))
        for host_ip, container_name in destory_params.items():
            if isinstance(container_name, str):
                self.__post(host_ip, container_name, admin_user, admin_passwd)
            elif isinstance(container_name, list):
                logging.info('container_name_list : %s' % str(container_name))
                for _name in container_name:
                    self.__post(host_ip, _name, admin_user, admin_passwd)
                    
    def __post(self, host_ip, container_name, admin_user, admin_passwd):
        args = {}
        args.setdefault('container_name', container_name)
        request_uri = 'http://%s:%s/container/remove' % (host_ip, options.port)
        logging.info('destory post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
        ret = http_post(request_uri, args, auth_username = admin_user, auth_password = admin_passwd)
        logging.info('destory result: %s' % str(ret))                   
    
    def __get_destory_params(self, containerClusterName):
        destory_params, container_name_list = {}, []
        container_ip_list = self.zkOper.retrieve_container_list(containerClusterName)
        for contaier_ip in container_ip_list:
            container_info = self.zkOper.retrieve_container_node_value(containerClusterName, contaier_ip)
            container_name = container_info.get('containerName')
            host_ip = container_info.get('hostIp')
            if host_ip in destory_params:
                container_name_list.append(container_name)
                container_name_list.append(destory_params[host_ip])
                destory_params[host_ip] = container_name_list
            else:
                destory_params.setdefault(host_ip, container_name)
        return destory_params

    
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
        
        create_container_arg_list = self.__get_container_params(containerCount, containerClusterName, adminUser, adminPasswd)
        
        create_container_node_ip_list = self.__choose_host()
        logging.info('choose host iplist: %s' % str(create_container_node_ip_list) )
        
        container_finished_flag_dict = self.__dispatch_create_container_task(create_container_node_ip_list, create_container_arg_list, 
                                                                                              containerCount, adminUser, adminPasswd)
        logging.info('create container result: %s' % str(container_finished_flag_dict))
                
        check_result = self.__check_result(create_container_node_ip_list, container_finished_flag_dict)
        logging.info('check_result: %s' % check_result)
        if not check_result:
            raise MyError('not all container succeed created')
        
        flag = self._check_mlcuster_manager_stat(create_container_node_ip_list, create_container_arg_list, 6)
        if flag:
            container_cluster_info = self.zkOper.retrieve_container_cluster_info(containerClusterName)
            container_cluster_info.setdefault('start_flag', 'succeed')
            self.zkOper.write_container_cluster_info(container_cluster_info)
            self._send_email("container", " container create operation finished on server cluster")
          
    def __retrieve_ip_resource(self, createContainerCount):
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
     
    def issue_create_container_request(self, host_ip,  args_dict, admin_user, admin_passwd):
        url_post = "/inner/container" 
        requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
        logging.info('requesturi:%s' % requesturi)
        logging.info('args_dict:%s' % args_dict)
        args_dict.setdefault('host_ip', host_ip)
        try:
            request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(args_dict), connect_timeout=40.0,\
                                  request_timeout=40.0, auth_username = admin_user, auth_password = admin_passwd)
            fetch_ret = _request_fetch(request)
            logging.info('POST result :%s' % str(fetch_ret))
            ret = eval(fetch_ret).get('response').get('message')
            if ret == 'Success Create Container':
                return True
        except:
            logging.error(str(traceback.format_exc()))
            return False
    
    def __get_container_params(self, containerCount, containerClusterName, adminUser, adminPasswd):

        create_container_arg_list = []
        try:
            containerIPList = self.__retrieve_ip_resource(containerCount)
        except:
            raise MyError('No ip in Ip pool, please add!')

#             logging.info('no ip in ip pool, add auto!')
#             data_node_list = self.zkOper.retrieve_data_node_list()
#             host_ip = random.choice(data_node_list)
#             url = 'http://%s:%s/containerCluster/ips' % (host_ip, options.port)
#             get_ret = http_get(url, auth_username=adminUser, auth_password=adminPasswd)
           
        
        volumes, binds = self.__get_normal_volumes_args(containerClusterName)
        for i in range(int(containerCount)):
            create_container_arg_dict, env = {}, {}
            create_container_arg_dict.setdefault('containerClusterName', containerClusterName)
            create_container_arg_dict['container_ip'] = containerIPList[i]
            container_name = 'd_mcl_%s_node_%s' % (containerClusterName, str(i+1))
            create_container_arg_dict['container_name'] = container_name
                        
            if i == int(containerCount-1):
                create_container_arg_dict['container_type'] = 'mclustervip'
            else:
                create_container_arg_dict['container_type'] = 'mclusternode'
                create_container_arg_dict.setdefault('volumes', volumes)
                create_container_arg_dict.setdefault('binds', binds)
                for j, containerIp in enumerate(containerIPList):
                    num = j+1
                    env.setdefault('N%s_IP' % str(num), containerIp)
                    env.setdefault('N%d_HOSTNAME' % num, 'd_mcl_%s_node_%s' % (containerClusterName, str(num+1)))
                    env.setdefault('ZKID', i+1)
            
            gateway = self.__get_gateway_from_ip(containerIp)
            env.setdefault('NETMASK', '255.255.255.0')
            env.setdefault('GATEWAY', gateway)
            env.setdefault('HOSTNAME', 'd_mcl_%s_node_%s' % (containerClusterName, str(i+1)))
            env.setdefault('IP', containerIPList[i])
            
            create_container_arg_dict.setdefault('env', env)
            create_container_arg_list.append(create_container_arg_dict)
        return create_container_arg_list
    
    def __get_normal_volumes_args(self, containerClusterName):
        volumes, binds = [], {}
        mcluster_conf_info = self.zkOper.retrieve_mcluster_info_from_config()
        logging.info('mcluster_conf_info: %s' % str(mcluster_conf_info))
        mount_dir = eval( mcluster_conf_info.get('mountDir') )
        for k,v in mount_dir.items():
            volumes.append(k)
            binds.setdefault(v, {'bind': k})
        return volumes, binds
    
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
                rst = _request_fetch(request)
                return_dict = json.loads(rst)
                resource_dict.setdefault(data_node_ip, return_dict['response'])
            logging.info("Before sort, all server the resource info, the resource value is %s" % str(resource_dict))
            create_container_node_ip_list = self._sort_server_resource(resource_dict)
            logging.info("After sort, the resource list is %s" % str(create_container_node_ip_list))
        return create_container_node_ip_list
        
    def __dispatch_create_container_task(self, create_container_node_ip_list,  create_container_arg_list, 
                                         container_count, admin_user, admin_passwd):
        logging.info('create_container_arg_list :%s' % str(create_container_arg_list))
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

    def _check_mlcuster_manager_stat(self, create_container_node_ip_list, create_container_arg_list, num):
        container_name_list = self.__get_containerName_list(create_container_arg_list)
        logging.info('wait 5 seconds...')
        time.sleep(5)
        while num:
            stat = True
            succ = {}
            for index,host_ip in enumerate(create_container_node_ip_list):
                container_name = container_name_list[index]
                ret = self.__get(container_name, host_ip)
                if ret:
                    succ.setdefault(host_ip, container_name)
                else:
                    stat = False
            if stat:
                logging.info('successful!!!')
                return True
            
            for hostip, containername in succ.items():
                container_name_list.remove(containername)
                create_container_node_ip_list.remove(hostip)
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
            request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40.0, request_timeout=40.0)
            fetch_ret = _request_fetch(request)
            logging.info('fetch_ret:%s' % str(fetch_ret))
            fetch_ret = json.loads(fetch_ret)
            logging.info('get type :%s' % str(type(fetch_ret) ) )
            ret = fetch_ret.get('response').get('message')
            logging.info('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
            logging.info('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
            return ret
        except:
            return False