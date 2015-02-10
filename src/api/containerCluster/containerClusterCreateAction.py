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
from resource.portOpers import PortOpers
from resource.resourceVerify import ResourceVerify
from utils.exceptions import CommonException
from utils.autoutil import http_get
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from container.container_model import Container_Model
from componentProxy.componentContainerModelFactory import ComponentContainerModelFactory
from componentProxy.componentContainerClusterConfigFactory import ComponentContainerClusterConfigFactory

class ContainerCluster_create_Action(Abstract_Async_Thread): 
    ip_opers = IpOpers()
    port_opers = PortOpers()
    
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
        _network_mode = _containerClusterName = args.get('network_mode')
        
        logging.info('containerClusterName : %s' % str(_containerClusterName))
        logging.info('_component_type : %s' % str(_component_type))
        logging.info('_network_mode : %s' % str(_network_mode))
        
        
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
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
                
        ip_port_resource_list = self.__get_ip_port_resource(_network_mode, containerCount)
        logging.info('ip_port_resource_list : %s' % str(ip_port_resource_list) )
        
        create_container_arg_list = self.component_container_model_factory.create(_component_type, 
                                                                                  args,
                                                                                  containerCount, 
                                                                                  _containerClusterName, 
                                                                                  ip_port_resource_list,
                                                                                  _component_container_cluster_config)


        create_container_node_ip_list = select_ip_list
        
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
            _action_flag = self.component_manager_status_validator.start_Status_Validator(_component_type, 
                                                                                          create_container_node_ip_list, 
                                                                                          create_container_arg_list, 
                                                                                          6)
        else:
            _action_flag = True
            
        _action_result = 'failed' if not _action_flag else 'succeed'
        
        return (_action_result, '')
        
    
    def __get_ip_port_resource(self, _network_mode, containerCount):
        ip_port_resource_list = []
        if 'ip' == _network_mode:
            ip_port_resource_list = self.ip_opers.retrieve_ip_resource(containerCount)
        elif 'port' == _network_mode:
            ip_port_resource_list = self.port_opers.retrieve_port_resource(containerCount)
        return ip_port_resource_list
    
    def __update_zk_info_when_process_complete(self, _containerClusterName, create_result='failed', error_msg=''):
        if _containerClusterName is None or '' == _containerClusterName:
            raise CommonException('_containerClusterName should be not null,in __updatez_zk_info_when_process_complete')
        
        _container_cluster_info = self.zkOper.retrieve_container_cluster_info(_containerClusterName)
        _container_cluster_info.setdefault('start_flag', create_result)
        _container_cluster_info.setdefault('error_msg', error_msg)
        self.zkOper.write_container_cluster_info(_container_cluster_info)
    
    def __create_container_cluser_info(self, containerCount, containerClusterName):
        _container_cluster_info = {}
        _container_cluster_info.setdefault('containerCount', containerCount)
        _container_cluster_info.setdefault('containerClusterName', containerClusterName)
        self.zkOper.write_container_cluster_info(_container_cluster_info)
    
    @tornado.gen.engine
    def __dispatch_create_container_task(self, create_container_node_ip_list, container_model_list, container_count):
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        _error_record_dict = {}
        try:
            _key_sets = set()
            for i in range(container_count):
                container_model = container_model_list[i]
                host_ip = create_container_node_ip_list[i]
                container_model.host_ip = host_ip
                property_dict = _get_property_dict(container_model)
                url_post = "/inner/container" 
                requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
                logging.debug('requesturi:%s' % requesturi)
                logging.debug('property dict before dispatch: %s' % str(property_dict) )
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(property_dict), \
                                      connect_timeout=40, request_timeout=40)
                
                callback_key = "%s_%s_%s" % ("create_container", _component_type, host_ip)
                _key_sets.add(callback_key)
                http_client.fetch(request, callback=(yield Callback(callback_key)))
            
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
    