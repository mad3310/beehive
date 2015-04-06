'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys
import tornado
import urllib
import time

from tornado.options import options
from tornado.gen import Callback, Wait
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from common.abstractAsyncThread import Abstract_Async_Thread
from resource_letv.ipOpers import IpOpers
from resource_letv.portOpers import PortOpers
from resource_letv.resource import Resource
from utils import _get_property_dict
from utils import handleTimeout, http_get
from utils.exceptions import CommonException
from utils import _retrieve_userName_passwd
from componentProxy.componentManagerValidator import ComponentManagerStatusValidator
from componentProxy.componentContainerModelFactory import ComponentContainerModelFactory
from componentProxy.componentContainerClusterConfigFactory import ComponentContainerClusterConfigFactory
from status.status_enum import Status
from zk.zkOpers import ZkOpers


class ContainerCluster_create_Action(Abstract_Async_Thread): 
    ip_opers = IpOpers()
    
    port_opers = PortOpers()
    
    resource = Resource()
    
    component_manager_status_validator = ComponentManagerStatusValidator()
    
    component_container_model_factory = ComponentContainerModelFactory()
    
    component_container_cluster_config_factory = ComponentContainerClusterConfigFactory()

    def __init__(self, arg_dict={}):
        super(ContainerCluster_create_Action, self).__init__()
        self._arg_dict = arg_dict

    def run(self):
        __action_result = Status.failed
        __error_message = ''
        _containerClusterName = self._arg_dict.get('containerClusterName')
        try:
            logging.debug('begin create')
            __action_result = self.__issue_create_action(self._arg_dict)
        except CommonException as e:
            __error_message = str(e)
            self.threading_exception_queue.put(e)
        except:
            self.threading_exception_queue.put(sys.exc_info())
        finally:
            '''
            set the action result to zk, if throw exception, the process will be shut and set 'failed' to zk. 
            The process is end.
            
            ***when container cluster is created failed, then such code will get a exception(handle this later)
            '''
            self.__update_zk_info_when_process_complete(_containerClusterName, __action_result, __error_message)

    def __issue_create_action(self, args={}):
        logging.info('args:%s' % str(args))
        _component_type = args.get('componentType')
        _network_mode = args.get('networkMode')
        
        logging.info('containerClusterName : %s' % str(args.get('containerClusterName')))
        logging.info('component_type : %s' % str(_component_type))
        logging.info('network_mode : %s' % str(_network_mode))
        
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        args.setdefault('component_config', _component_container_cluster_config)
        
        self.__create_container_cluser_info_to_zk(_network_mode, _component_container_cluster_config)
        
        host_ip_list = self.resource.elect_servers(_component_container_cluster_config)
        
        is_res_verify = _component_container_cluster_config.is_res_verify
        if is_res_verify:
            '''
            @todo: why remove the self.res_verify.get_create_containers_hostip_list(usable_hostip_num_list, _component_container_cluster_config)
            '''
            self.resource.validateResource(_component_container_cluster_config)

        logging.info('host_ip_list:%s' % str(host_ip_list))
        args.setdefault('host_ip_list', host_ip_list)
        
        ip_port_resource_list = self.resource.retrieve_ip_port_resource(host_ip_list, _component_container_cluster_config)
        args.setdefault('ip_port_resource_list', ip_port_resource_list)
        
        logging.info('show args to get create containers args list: %s' % str(args))
        container_model_list = self.component_container_model_factory.create(args)
        
        self.__dispatch_create_container_task(container_model_list)
        
        '''
        @todo: what means use below logic? __dispatch_create_container_task don't confirm the container start status?
        '''
        started = self.__check_cluster_started(_component_container_cluster_config)
        if not started:
            raise CommonException('cluster started failed, maybe part of nodes started, other failed!')
        
        _action_flag = True
        if _component_container_cluster_config.need_validate_manager_status:
            _action_flag = self.component_manager_status_validator.validate_manager_status_for_cluster(_component_type, container_model_list)
        
        logging.info('validator manager status result:%s' % str(_action_flag))
        _action_result = Status.failed if not _action_flag else Status.succeed
        return _action_result

    def __check_cluster_started(self, component_container_cluster_config):
        '''
        @todo: why sleep 8 seconds?
        '''
        logging.info('time sleep 8 seconds')
        time.sleep(8)
        container_cluster_name = component_container_cluster_config.container_cluster_name
        
        '''
        @todo: why handlerTimeout?
        '''
        return handleTimeout(self.__is_cluster_started, 120, container_cluster_name)
    
    def __is_cluster_started(self, container_cluster_name):
        '''
        @todo: why use http way, only invoke this method to check status.
        '''
        adminUser, adminPasswd = _retrieve_userName_passwd()
        uri_get = '/containerCluster/status/%s' % container_cluster_name
        uri = 'http://localhost:%s%s' % (options.port, uri_get)
        
        ret = http_get(uri, auth_username=adminUser, auth_password=adminPasswd)
        logging.info('get cluster is started result :%s, type:%s' % (str(ret), type(ret)) )
        status = ret.get('response').get('status')
        return status == Status.started

    def __update_zk_info_when_process_complete(self, _containerClusterName, create_result='failed', error_msg=''):
        if _containerClusterName is None or '' == _containerClusterName:
            raise CommonException('_containerClusterName should be not null,in __updatez_zk_info_when_process_complete')
        
        zkOper = ZkOpers()
        try:
            _container_cluster_info = zkOper.retrieve_container_cluster_info(_containerClusterName)
            _container_cluster_info.setdefault('start_flag', create_result)
            _container_cluster_info.setdefault('error_msg', error_msg)
            _container_cluster_info.setdefault('containerClusterName', _containerClusterName)
            zkOper.write_container_cluster_info(_container_cluster_info)
        finally:
            zkOper.close()
        

    def __create_container_cluser_info_to_zk(self, network_mode, component_container_cluster_config):
        containerCount = component_container_cluster_config.nodeCount
        containerClusterName = component_container_cluster_config.container_cluster_name
        
        _container_cluster_info = {}
        _container_cluster_info.setdefault('containerCount', containerCount)
        _container_cluster_info.setdefault('containerClusterName', containerClusterName)
        use_ip = True
        if 'bridge' == network_mode:
            use_ip = False
        _container_cluster_info.setdefault('use_ip', use_ip)
        
        zkOper = ZkOpers()
        try:
            zkOper.write_container_cluster_info(_container_cluster_info)
        finally:
            zkOper.close()
        

    @tornado.gen.engine
    def __dispatch_create_container_task(self, container_model_list):
        http_client = AsyncHTTPClient()
        _error_record_dict = {}
        adminUser, adminPasswd = _retrieve_userName_passwd()
        try:
            _key_sets = set()
            for index, container_model in enumerate(container_model_list):
                property_dict = _get_property_dict(container_model)
                host_ip = property_dict.get('host_ip')
                url_post = "/inner/container"
                requesturi = "http://%s:%s%s" % (host_ip, options.port, url_post)
                logging.info('requesturi:%s' % requesturi)
                logging.info('property dict before dispatch: %s' % str(property_dict) )
                request = HTTPRequest(url=requesturi, method='POST', body=urllib.urlencode(property_dict), \
                                      connect_timeout=40, request_timeout=40, auth_username=adminUser, auth_password=adminPasswd)
                
                callback_key = "%s_%s" % ("create_container", host_ip)
                _key_sets.add(callback_key)
                http_client.fetch(request, callback=(yield Callback(callback_key)))
            
            for i in range(len(container_model_list)):
                callback_key = _key_sets.pop()
                response = yield Wait(callback_key)
                
                if response.error:
                    return_result = False
                    error_record_msg = "remote access,the key:%s,error message:%s" % (callback_key,response.error)
                else:
                    return_result = response.body.strip()
                
                if cmp('false', return_result) == 0:
                    callback_key_ip = callback_key.split("_")[-1]
                    _error_record_dict.setdefault(callback_key_ip, error_record_msg)

            if len(_error_record_dict) > 0:
                raise CommonException('not all container succeed created %s' % str(_error_record_dict))
            else:
                logging.info('task create all containers are dispatched!')
                    
        finally:
            http_client.close()
