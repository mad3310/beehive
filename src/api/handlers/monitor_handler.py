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
from tornado_letv.tornado_basic_auth import require_basic_auth
from server.serverOpers import Server_Opers
from utils.exceptions import HTTPAPIError


# retrieve the status value of all monitor type 
# eg. curl "http://localhost:8888/mcluster/status"          
class ContainerStatus(APIHandler):
    
    def get(self):
        
        monitor_types = self.zkOper.retrieve_monitor_type()
        stat_dict = {}
        for monitor_type in monitor_types:
            monitor_status_list = self.zkOper.retrieve_monitor_status_list(monitor_type)
            
            monitor_type_sub_dict = {}
            for monitor_status_key in monitor_status_list:
                monitor_status_value = self.zkOper.retrieve_monitor_status_value(monitor_type, monitor_status_key)
                monitor_type_sub_dict.setdefault(monitor_status_key, monitor_status_value)
                
            stat_dict.setdefault(monitor_type, monitor_type_sub_dict)

        self.finish(stat_dict)


class CheckServerContainersMemLoad(APIHandler):
    
    server_opers = Server_Opers()
    
    def get(self):
        
        logging.info('server: %s' % self.request.remote_ip)
        cons_mem_load = {}
        try:
            cons_mem_load = self.server_opers.get_all_containers_mem_load()
        except:
            logging.error( str( traceback.format_exc() ) )
            raise HTTPAPIError(status_code=500, error_detail="code error!",\
                               notification = "direct", \
                               log_message= "code error!",\
                               response =  "code error!")
        
        logging.info('get server %s containers memory load :%s' % (self.request.remote_ip, str(cons_mem_load) ) )
        self.finish( cons_mem_load )


@require_basic_auth
class CheckServersContainersMemLoad(APIHandler):
    
    @asynchronous
    @engine
    def get(self):
        
        async_client = AsyncHTTPClient()
        server_list = self.zkOper.retrieve_servers_white_list()
        
        server_cons_mem_load = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/inner/monitor/server/containers/memory' % (server, options.port)
                logging.info('server requesturi: %s' % str(requesturi))
                response = yield Task(async_client.fetch, requesturi)
                logging.info('mem response body: %s' % str(response.body) )
                body = json.loads(response.body.strip())
                con_mem_load = body.get('response')
                server_cons_mem_load.setdefault(server, con_mem_load)
        except:
            error_msg = str(traceback.format_exc())
            raise HTTPAPIError(status_code=500, error_detail="code error!",\
                               notification = "direct", \
                               log_message= "code error!",\
                               response =  {"code error":error_msg} )
        finally:
            async_client.close()
            
        self.finish( server_cons_mem_load )


class CheckServerContainersUnderOom(APIHandler):
    
    server_opers = Server_Opers()
    
    def get(self):
        server_ip = self.request.remote_ip
        cons_under_oom = {}
        
        illegal_containers = self.server_opers.get_all_containers_under_oom()
        cons_under_oom.setdefault('illegal_containers', illegal_containers)
        
        logging.debug('get server %s containers memory load :%s' % (server_ip, str(cons_under_oom) ) )
        self.finish( cons_under_oom )

'''
@todo: 
1. the different with above logic?
'''
@require_basic_auth
class CheckServersContainersUnderOom(APIHandler):
    
    @asynchronous
    @engine
    def get(self):
        
        async_client = AsyncHTTPClient()
        server_list = self.zkOper.retrieve_servers_white_list()
        
        server_cons_under_oom = {}
        try:
            for server in server_list:
                requesturi = 'http://%s:%s/inner/monitor/server/containers/under_oom' % (server, options.port)
                logging.debug('server requesturi: %s' % str(requesturi))
                response = yield Task(async_client.fetch, requesturi)
                body = json.loads(response.body.strip())
                logging.info('response body : %s' % str(body) )
                under_oom = body.get('response')
                if not isinstance(under_oom, dict):
                    under_oom = {'serverError': ['code error']}
                server_cons_under_oom.setdefault(server, under_oom)
        except:
            error_msg = str(traceback.format_exc())
            raise HTTPAPIError(status_code=500, error_detail="code error!",\
                               notification = "direct", \
                               log_message= "code error!",\
                               response = {"code error":error_msg} )
        finally:
            async_client.close()
        
        self.finish( server_cons_under_oom )
