'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys
import tornado

from tornado.options import options
from tornado.gen import Callback, Wait
from common.abstractAsyncThread import Abstract_Async_Thread
from resource.ipOpers import IpOpers
from resource.resourceVerify import ResourceVerify
from utils.exceptions import CommonException
from utils.autoutil import http_get
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from container.container_model import Container_Model
from componentProxy.componentContainerModelFactory import ComponentContainerModelFactory

class ContainerCluster_create_Action(Abstract_Async_Thread): 
    ip_opers = IpOpers()
    
    res_verify = ResourceVerify()
    
    component_manager_status_validator = ComponentManagerStatusValidator()
    
    component_container_model_factory = ComponentContainerModelFactory()
    
    component_container_cluster_config_factory = ComponentContainerClusterConfigFactory()
    
    def __init__(self, arg_dict={}):
        super(ContainerCluster_create_Action, self).__init__()
        self._arg_dict = arg_dict
        
    def run(self):
        __action_result = 'failed'
        __error_message = ''
        _containerClusterName = self._arg_dict.get('containerClusterName')
        try:
            logging.debug('begin create')
            __action_result, __error_message = self.__issue_create_action(self._arg_dict)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            '''
            set the action result to zk, if throw exception, the process will be shut and set 'failed' to zk. 
            The process is end.
            '''
            self.__update_zk_info_when_process_complete(_containerClusterName, __action_result, __error_message='')
  
    def __issue_create_action(self, args={}):
        logging.info('args:%s' % str(args))
        _containerClusterName = args.get('containerClusterName')
        _component_type = args.get('componentType')
        logging.info('containerClusterName : %s' % str(_containerClusterName))
        
        
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config()
        logging.info('config node info in zk: %s, type: %s' % ( str( _component_container_cluster_config), type(_component_container_cluster_config)) )
        
        
        is_res_verify = _component_container_cluster_config.is_res_verify
        containerCount = _component_container_cluster_config.nodeCount
        self.__create_container_cluser_info(containerCount, _containerClusterName)
        
        select_ip_list = []
        if is_res_verify:
            ret = self.res_verify.check_resource(_component_container_cluster_config)
            _error_msg = ret.get('error_msg')
            '''
            @todo: 
            1. check_resource return dict type message, could the error_message be put to the client?
            2. why put the lack_resource to the client?
            '''
            if _error_msg:
                _action_result = 'lack_resource'
                return (_action_result, _error_msg)
            else:
                select_ip_list = ret.get('select_ip_list')
                logging.info('select_ip_list:%s' % str(select_ip_list))
                
        '''
        @todo: retrieve ip or port, then put these ip or port to create method
        '''
        
        create_container_arg_list = self.component_container_model_factory.create(_component_type, 
                                                                                  args, 
                                                                                  containerCount, 
                                                                                  _containerClusterName)

        '''
        @todo: the select_ip_list exist, why use __choose_host() to retrieve the host list?
        '''
        if select_ip_list:
            create_container_node_ip_list = select_ip_list
        else:
            create_container_node_ip_list = self.__choose_host()
        
        logging.info('choose host iplist: %s' % str(create_container_node_ip_list) )
        
        _error_record_dict = self.__dispatch_create_container_task(create_container_node_ip_list, 
                                                                   create_container_arg_list, 
                                                                   containerCount)
                      
        if _error_record_dict.__len__() <> 0:
            raise CommonException('not all container succeed created %s' % str(_error_record_dict))
        else:
            logging.info('all container create successful')
        
        _action_flag = False
        if _component_container_cluster_config.need_validate_manager_status:
            _action_flag = self.component_manager_status_validator(_component_type, 
                                                                   create_container_node_ip_list, 
                                                                   create_container_arg_list, 
                                                                   6)
        else:
            _action_flag = True
            
        _action_result = 'failed' if not _action_flag else 'succeed'
        
        return (_action_result, '')
        
            
    def __update_zk_info_when_process_complete(self, _containerClusterName, create_result='failed', error_msg):
        if _containerClusterName is None or '' == _containerClusterName:
            raise CommonException('_containerClusterName should be not null,in __updatez_zk_info_when_process_complete')
        
        container_cluster_info = self.zkOper.retrieve_container_cluster_info(_containerClusterName)
        container_cluster_info.setdefault('start_flag', create_result)
        container_cluster_info.setdefault('error_msg', error_msg)
        self.zkOper.write_container_cluster_info(container_cluster_info)
    
    def __create_container_cluser_info(self, containerCount, containerClusterName):
        containerClusterProps = {}
        containerClusterProps.setdefault('containerCount', containerCount)
        containerClusterProps.setdefault('containerClusterName', containerClusterName)
        self.zkOper.write_container_cluster_info(containerClusterProps)
    
    @tornado.gen.engine
    def __dispatch_create_container_task(self, create_container_node_ip_list, create_container_arg_list, container_count):
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        _error_record_dict = {}
        try:
            _key_sets = set()
            for i in range(container_count):
                args_dict = create_container_arg_list[i]
                host_ip = create_container_node_ip_list[i]
                args_dict.setdefault('host_ip', host_ip)
                url_post = "/inner/container" 
                requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
                logging.debug('requesturi:%s' % requesturi)
                logging.debug('args_dict:%s' % args_dict)
                callback_key = "%s_%s_%s" % ("create_container", _component_type, host_ip)
                _key_sets.add(callback_key)
                http_client.fetch(requesturi, callback=(yield Callback(callback_key)))
            
        
            for i in range(container_count):
                callback_key = _key_sets.pop()
                response = yield Wait(callback_key)
                
                if response.error:
                    return_result = False
                    error_record_msg = "remote access,the key:%s,error message:%s" % (callback_key,response.error)
                else:
                    return_result = response.body.strip()
                
                if cmp('false',return_result) == 0:
                    callback_key_ip = callback_key.split("_")[-1]
                    _error_record_dict.setdefault(callback_key_ip, error_record_msg)
                    
        finally:
            http_client.close()
            
        return _error_record_dict
    
    def __choose_host(self):
        create_container_node_ip_list = []
        data_node_info_list = self.zkOper.retrieve_data_node_list()
        data_node_info_list.sort()
        '''
        @todo: don't use 4 to compare the container list
        '''
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
            create_container_node_ip_list = self.__sort_server_resource(resource_dict)
            logging.info("After sort, the resource list is %s" % str(create_container_node_ip_list))
        return create_container_node_ip_list
    
    def __sort_server_resource(self, arg_dict):
        resource_list = []
        create_node_ip_list = []
        for (data_node_ip, resource_sub_dict) in arg_dict.items():
            memoryCount = resource_sub_dict.get('memoryCount')
            diskCount = resource_sub_dict.get('diskCount')
            resourceCount = memoryCount * 0.6 + diskCount *0.4
            resource_list.append(resourceCount)
        resource_list.sort()
        for resourceCount in resource_list:
            for (data_node_ip, resource_sub_dict) in arg_dict.items():
                memoryCount = resource_sub_dict.get('memoryCount')
                diskCount = resource_sub_dict.get('diskCount')
                resourceCount_cal_tmp = memoryCount * 0.6 + diskCount *0.4
                if resourceCount_cal_tmp == resourceCount:
                    create_node_ip_list.insert(0,data_node_ip)
                    del arg_dict[data_node_ip]
                    break
        return create_node_ip_list
    
    