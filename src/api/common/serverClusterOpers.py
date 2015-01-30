#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys
import logging
import traceback
import tornado.httpclient

from zkOpers import ZkOpers
from tornado.options import options
from tornado.gen import Callback, Wait
from abstractAsyncThread import Abstract_Async_Thread
from utils.autoutil import *


class ServerCluster_Opers(Abstract_Async_Thread):
    '''
    classdocs
    '''
    def __init__(self):
        pass
    
    def update(self):
        try:
            logging.info('do update server!')
            self._update()
        except:
            logging.error( str(traceback.format_exc()) )
            self.threading_exception_queue.put(sys.exc_info())
    
    @tornado.gen.engine
    def _update(self):

        http_client = tornado.httpclient.AsyncHTTPClient()
          
        succ, fail, return_result  = [], [], ''
        key_sets = set()
        server_list = self.zkOper.retrieve_data_node_list()
         
        for server in server_list:
            requesturi = 'http://%s:%s/inner/server/update' % (server, options.port)
            logging.info('server requesturi: %s' % str(requesturi))
            callback_key = server
            key_sets.add(callback_key)
            http_client.fetch(requesturi, callback=(yield Callback(callback_key)))
        
        logging.info('key_sets:%s' % str(key_sets) )
        
        error_record = ''
        for i in range(len(key_sets)):
            callback_key = key_sets.pop()
            response = yield Wait(callback_key)
            if response.error:
                message = "remote access, the key:%s,\n error message:\n %s" % (callback_key, str(response.error) )
                error_record += message + "|"
                logging.error(error_record)
            else:
                return_result = response.body.strip()
            
            if return_result:
                logging.info('return_result : %s' % str(return_result) )
                succ.append(callback_key)
            else:
                fail.append(callback_key)
        
        http_client.close()
        logging.info('succ:%s' % str(succ))
        logging.info('fail:%s' % str(fail))




