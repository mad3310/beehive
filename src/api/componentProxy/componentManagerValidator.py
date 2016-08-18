'''
Created on 2015-2-4

@author: asus
'''

import importlib
import logging
import time

from componentProxy import _path
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from tornado.options import options
from utils import http_post


class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''

    global executor
    executor = ThreadPoolExecutor(max_workers=10)

    def __init__(self):
        '''
        Constructor
        '''

    def validate_manager_status_for_container(self, component_type, container_name):
        _check_result = False
        _component_path = _path.get(component_type)

        module_path = '%s.%s.%sOper' % (_component_path, component_type, component_type)
        
        cls_name = '%sManager' % component_type.capitalize()
        
        module_obj = importlib.import_module(module_path)
        manager_validator = getattr(module_obj, cls_name)()
        
        _check_result = manager_validator.manager_status(container_name)
        return _check_result
    
    def validate_manager_status_for_cluster(self, component_type, container_model_list, retry_num = 6):
        post_arg_list = []
        for container_model in container_model_list:
            host_ip = container_model.host_ip
            container_name = container_model.container_name
            
            _body = {}
            _body.setdefault('containerName', container_name)
            _body.setdefault('componentType', component_type)
            
            logging.info('host_ip:%s, container_name:%s' % (host_ip, container_name))
            uri = "/container/manager/status"
            url = "http://%s:%s%s" % (host_ip, options.port, uri)
            post_arg_list.append((url, _body))
        
        while retry_num:
            self.__executor(post_arg_list)
            if not post_arg_list:
                return True
            
            retry_num -= 1
            time.sleep(10)
            
        return False

    def __executor(self, post_arg_list):
        succ_list = []
        
        fs = dict( (executor.submit(http_post, _url, _body),  (_url,_body)) for (_url,_body) in post_arg_list )
        logging.info('future dict :%s' % str(fs) )
        
        for future in futures.as_completed(fs):
            if future.exception() is not None:
                logging.info('expection:%s' % future.exception() )
            else:
                fetch_ret = future.result()
                logging.info('fetch_ret:%s' % str(fetch_ret))
                ret = fetch_ret.get('response').get('message')
                logging.debug('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
                logging.debug('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
                if ret:
                    (_url,_body) = fs[future]
                    succ_list.append((_url,_body))
                        
        for succ in succ_list:
            post_arg_list.remove(succ)
