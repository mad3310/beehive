#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

import logging
import traceback
import json

from base import APIHandler
from tornado.web import asynchronous
from tornado.gen import Task, engine
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options
from common.tornado_basic_auth import require_basic_auth
from common.serverOpers import Server_Opers
from common.zkOpers import ZkOpers


# retrieve the status value of all monitor type 
# eg. curl "http://localhost:8888/mcluster/status"          
class ContainerStatus(APIHandler):
    
    @asynchronous
    def get(self):
        
        monitor_types = self.zkOper.retrieve_monitor_type()
        stat_dict = {}
        for monitor_type in monitor_types:
            monitor_status_list = self.zkOper.retrieve_monitor_status_list(monitor_type)
            monitor_status_list_count = len(monitor_status_list)
            
            monitor_type_sub_dict = {}
            for monitor_status_key in monitor_status_list:
                monitor_status_value = self.zkOper.retrieve_monitor_status_value(monitor_type, monitor_status_key)
                monitor_type_sub_dict.setdefault(monitor_status_key, monitor_status_value)
                
            stat_dict.setdefault(monitor_type, monitor_type_sub_dict)

        self.finish(stat_dict)


class CheckServerContainersMemLoad(APIHandler):
    
    server_opers = Server_Opers()
    
    @asynchronous
    def get(self):
        
        logging.info('server: %s' % self.request.remote_ip)
        cons_mem_load = {}
        try:
            cons_mem_load = self.server_opers.get_all_containers_mem_load()
        except:
            logging.error( str( traceback.format_exc() ) )
        
        logging.info('get server %s containers memory load :%s' % (self.request.remote_ip, str(cons_mem_load) ) )
        self.finish( cons_mem_load )


@require_basic_auth
class CheckServersContainersMemLoad(APIHandler):
    
    zkOpers = ZkOpers('127.0.0.1', 2181)
    
    @asynchronous
    @engine
    def get(self):
        
        async_client = AsyncHTTPClient()
        server_list = self.zkOpers.retrieve_servers_white_list()
        
        server_cons_mem_load = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/monitor/server/containers/memory' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                response = yield Task(async_client.fetch, requesturi)
                body = json.loads(response.body.strip())
                logging.info('response body : %s' % str(body) )
                con_mem_load = body.get('response')
                server_cons_mem_load.setdefault(server, con_mem_load)
        except:
            logging.error( str(traceback.format_exc() ) )
            
        async_client.close()
        self.finish( server_cons_mem_load )


class CheckServerContainersUnderOom(APIHandler):
    
    server_opers = Server_Opers()
    
    @asynchronous
    def get(self):
        
        server_ip = self.request.remote_ip
        cons_under_oom = {}
        try:
            illegal_containers = self.server_opers.get_all_containers_under_oom()
            cons_under_oom.setdefault('illegal_containers', illegal_containers)
        except:
            logging.error( str( traceback.format_exc() ) )
        
        logging.info('get server %s containers memory load :%s' % (server_ip, str(cons_under_oom) ) )
        self.finish( cons_under_oom )


@require_basic_auth
class CheckServersContainersUnderOom(APIHandler):
    
    zkOper = ZkOpers('127.0.0.1', 2181)
    
    @asynchronous
    @engine
    def get(self):
        
        async_client = AsyncHTTPClient()
        server_list = self.zkOper.retrieve_servers_white_list()
        
        server_cons_under_oom = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/monitor/server/containers/under_oom' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                response = yield Task(async_client.fetch, requesturi)
                body = json.loads(response.body.strip())
                logging.info('response body : %s' % str(body) )
                under_oom = body.get('response')
                server_cons_under_oom.setdefault(server, under_oom)
        except:
            logging.error( str(traceback.format_exc() ) )
        
        async_client.close()
        #self.zkOper.close()
        self.finish( server_cons_under_oom )
