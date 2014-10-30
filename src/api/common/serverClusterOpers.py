#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import logging
import traceback
import tornado.httpclient

from abstractContainerOpers import Abstract_Container_Opers
from zkOpers import ZkOpers
from tornado.options import options
from tornado.gen import Callback, Wait
from abstractAsyncThread import Abstract_Async_Thread
from utils.autoutil import *


class ServerCluster_Opers(object):
    '''
    classdocs
    '''
    zkOper = ZkOpers('127.0.0.1', 2181)
    
    def __init__(self):
        pass
    
    @tornado.gen.engine
    def update(self):
        logging.info('run update')
        http_client = tornado.httpclient.AsyncHTTPClient()
          
        succ, fail = [], []
        key_sets = set()
        server_list = self.zkOper.retrieve_data_node_list()
         
        for server in server_list:
            requesturi = 'http://%s:%s/inner/server/update' % (server, options.port)
            callback_key = server
            key_sets.add(callback_key)
            http_client.fetch(requesturi, callback=(yield Callback(callback_key)))
         
        logging.info('key_sets:%s' % str(key_sets) )
        
        for i in range(len(key_sets)):
            callback_key = key_sets.pop()
            response = yield Wait(callback_key)
            if response.error:
                message = "remote access, the key:%s, error message:%s" % (callback_key, response.error)
                error_record += message + "|"
                logging.error(message)
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
