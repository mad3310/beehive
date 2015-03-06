#-*- coding: utf-8 -*-

import logging
import tornado

from tornado.options import options
from utils.autoutil import http_get
from tornado.gen import Callback, Wait
from tornado.httpclient import HTTPRequest, AsyncHTTPClient


class MclusterManagerValidator(object):
    
    def __init__(self, container_model_list):
        self.container_model_list = container_model_list
    
    def validate_manager_status(self, num):
        logging.info('begin validate manager status!')
        while num:
            logging.info('self.container_model_list length :%s' % len(self.container_model_list))
            if self.container_model_list:
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
    
    @tornado.gen.engine
    def __dispatch_task(self):
        http_client = AsyncHTTPClient()
        succ_list = []
        try:
            _key_sets = set()
            for container_model in self.container_model_list:
                host_ip = container_model.host_ip
                container_name = container_model.container_name
                url_get = "/inner/MclusterManager/status/%s" % container_name
                requesturi = "http://%s:%s%s" % (host_ip, options.port, url_get)
                logging.info('get request,  requesturi:%s' % requesturi)
                request = HTTPRequest(url=requesturi, method='GET', connect_timeout=40, request_timeout=40)
                callback_key = "%s_%s" % ("create_container", host_ip)
                _key_sets.add(callback_key)
                http_client.fetch(request, callback=(yield Callback(callback_key)))
            
            for container_model in self.container_model_list:
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
    