#-*- coding: utf-8 -*-

import logging
from tornado.options import options
from utils.autoutil import http_get
from tornado.gen import Callback, Wait
from tornado.httpclient import HTTPRequest, AsyncHTTPClient


class MclusterManagerValidator():
    
    def __init__(self, container_model_list):
        self.container_model_list = container_model_list
    
    def validate_manager_status(self, num):
        
        while num:
            stat = True
            if self.container_model_list:
                for i in len(self.container_model_list):
                    self.__dispatch_task()
            else:
                logging.info('successful!!!')
                return True
            num -= 1
    
#     def __get(self, containerName, container_node):
#         ret = False
#         url_post = "/inner/MclusterManager/status/%s" % containerName
#         requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
#         logging.debug('requesturi: %s' % requesturi)
#         fetch_ret = http_get(requesturi)
#         logging.info('fetch_ret:%s' % str(fetch_ret))
#         ret = fetch_ret.get('response').get('message')
#         logging.debug('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
#         logging.debug('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
#         return ret
    
    def __dispatch_task(self):
        http_client = tornado.httpclient.AsyncHTTPClient()
        succ_list = []
        try:
            _key_sets = set()
            for index, container_model in enumerate(self.container_model_list):
                property_dict = _get_property_dict(container_model)
                host_ip = container_model.host_ip
                container_name = container_model.container_name
                url_get = "/inner/MclusterManager/status/%s" % containerName
                requesturi = "http://%s:%s%s" % (host_ip, options.port, url_get)
                logging.info('get request,  requesturi:%s' % requesturi)
                request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40, request_timeout=40)
                callback_key = "%s_%s" % ("create_container", host_ip)
                _key_sets.add(callback_key)
                http_client.fetch(request, callback=(yield Callback(callback_key)))
            
            for container_model in len(self.container_model_list):
                callback_key = _key_sets.pop()
                response = yield Wait(callback_key)
                
                if response.error:
                    return_result = False
                    error_record_msg = "remote access,the key:%s,error message:%s" % (callback_key,response.error)
                else:
                    return_result = response.body.strip()
                    logging.info('mcluster status result:%s' % str(return_result) )
                    ret = return_result.get('response').get('message')
                    logging.debug('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
                
                if cmp(True, ret) == 0:
                    succ_list.append(container_model)
            
            for succ in succ_list:
                self.container_model_list.remove(succ)
                    
        finally:
            http_client.close()
        
        
        
        
    
    