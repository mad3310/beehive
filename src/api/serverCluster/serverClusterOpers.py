#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging

from tornado.options import options
from tornado.gen import Callback, Wait, engine
from tornado.httpclient import AsyncHTTPClient
from zk.zkOpers import ZkOpers
from utils import dispatch_mutil_task


class ServerCluster_Opers(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
            constructor
        '''
    
    @engine
    def update(self):

        http_client = AsyncHTTPClient()
          
        succ, fail, return_result  = [], [], ''
        key_sets = set()
        
        zkOper = ZkOpers()
        try:
            server_list = zkOper.retrieve_data_node_list()
        finally:
            zkOper.close()
        
        try: 
            for server in server_list:
                requesturi = 'http://%s:%s/inner/server/update' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                callback_key = server
                key_sets.add(callback_key)
                http_client.fetch(requesturi, callback=(yield Callback(callback_key)))
            
            logging.debug('key_sets:%s' % str(key_sets) )
            
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
                    logging.debug('return_result : %s' % str(return_result) )
                    succ.append(callback_key)
                else:
                    fail.append(callback_key)
        finally:
            http_client.close()
            
        logging.debug('succ:%s' % str(succ))
        logging.debug('fail:%s' % str(fail))
