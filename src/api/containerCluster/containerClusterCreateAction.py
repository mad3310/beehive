'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys
import tornado
import urllib

from tornado.options import options
from tornado.gen import Callback, Wait
from tornado.httpclient import HTTPRequest
from common.abstractAsyncThread import Abstract_Async_Thread
from resource_letv.ipOpers import IpOpers
from resource_letv.portOpers import PortOpers
from resource_letv.resourceVerify import ResourceVerify
from utils import _get_property_dict
from utils.exceptions import CommonException
from utils import _retrieve_userName_passwd
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
#            import traceback
#            logging.error(str(traceback.format_exc()))
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
        
        logging.info('containerClusterName : %s' % str(args.get('containerClusterName')))
        logging.info('_component_type : %s' % str(_component_type))
        logging.info('_network_mode : %s' % str(args.get('network_mode')))
        
        _component_container_cluster_config = self.component_container_cluster_config_factory.retrieve_config(args)
        args.setdefault('component_config', _component_container_cluster_config)
        
        is_res_verify = _component_container_cluster_config.is_res_verify
        logging.info('is_res_verify : %s' % str(is_res_verify) )
        
        host_ip_list = []
        if is_res_verify:
            try:
                usable_hostip_num_list = self.res_verify.check_resource(_component_container_cluster_config)
                host_ip_list = self.res_verify.get_create_containers_hostip_list(usable_hostip_num_list)
            except CommonException as e:
                return ('lack_resource', e)
        
        logging.info('host_ip_list:%s' % str(host_ip_list))
        args.setdefault('host_ip_list', host_ip_list)
        
        ip_port_resource_list = self.__get_ip_port_resource(_component_container_cluster_config)
        args.setdefault('ip_port_resource_list', ip_port_resource_list)
        
        logging.info('show args to get create containers args list: %s' % str(args) )
        container_model_list = self.component_container_model_factory.create(args)
        
        self.__write_container_cluser_info(_component_container_cluster_config)
        
        self.__dispatch_create_container_task(container_model_list)
        
        _action_flag = False
        if _component_container_cluster_config.need_validate_manager_status:
            _action_flag = self.component_manager_status_validator.start_Status_Validator(_component_type, container_model_list, 6)
        else:
            _action_flag = True
            
        _action_result = 'failed' if not _action_flag else 'succeed'
        
        return (_action_result, '')

    def __get_ip_port_resource(self, component_container_cluster_config):
        containerCount = component_container_cluster_config.nodeCount
        network_mode = component_container_cluster_config.network_mode 
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
    
    def __write_container_cluser_info(self, component_container_cluster_config):
        _container_cluster_info = {}
        containerCount = component_container_cluster_config.nodeCount
        containerClusterName = component_container_cluster_config.container_cluster_name
        _container_cluster_info.setdefault('containerCount', containerCount)
        _container_cluster_info.setdefault('containerClusterName', containerClusterName)
        self.zkOper.write_container_cluster_info(_container_cluster_info)
    
    @tornado.gen.engine
    def __dispatch_create_container_task(self, container_model_list):
        http_client = tornado.httpclient.AsyncHTTPClient()
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

            if _error_record_dict.__len__() <> 0:
                raise CommonException('not all container succeed created %s' % str(_error_record_dict))
            else:
                logging.info('all container create successful')
                    
        finally:
            http_client.close()    
    
