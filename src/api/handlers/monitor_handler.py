#-*- coding: utf-8 -*-

'''
Created on 2013-7-21

@author: asus
'''

import logging
import json

from base import APIHandler
from tornado.web import asynchronous
from tornado.gen import Task, engine
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options
from tornado_letv.tornado_basic_auth import require_basic_auth
from server.serverOpers import Server_Opers
from zk.zkOpers import ZkOpers


# retrieve the status value of all monitor type 
# eg. curl "http://localhost:8888/mcluster/status"          
class ContainerStatus(APIHandler):
    
    def get(self):
        zkOper = ZkOpers()
        
        try:
            monitor_types = zkOper.retrieve_monitor_type()
            stat_dict = {}
            for monitor_type in monitor_types:
                monitor_status_list = zkOper.retrieve_monitor_status_list(monitor_type)
                
                monitor_type_sub_dict = {}
                for monitor_status_key in monitor_status_list:
                    monitor_status_value = zkOper.retrieve_monitor_status_value(monitor_type, monitor_status_key)
                    monitor_type_sub_dict.setdefault(monitor_status_key, monitor_status_value)
                    
                stat_dict.setdefault(monitor_type, monitor_type_sub_dict)
        finally:
            zkOper.close()

        self.finish(stat_dict)


class CheckServerContainersUnderOom(APIHandler):
    """
        is invoked by CheckServersContainersUnderOom below
    """
    
    server_opers = Server_Opers()
    
    def get(self):
        server_ip = self.request.remote_ip
        cons_under_oom = {}
        
        illegal_containers = self.server_opers.get_all_containers_under_oom()
        cons_under_oom.setdefault('illegal_containers', illegal_containers)
        
        logging.debug('get server %s containers memory load :%s' % (server_ip, str(cons_under_oom) ) )
        self.finish( cons_under_oom )


@require_basic_auth
class CheckServersContainersUnderOom(APIHandler):
    """
        dispatch request to run on server, 
        then invoke the class CheckServerContainersUnderOom
    """
    
    @asynchronous
    @engine
    def get(self):
        zkOper = ZkOpers()
        
        try:
            server_list = zkOper.retrieve_servers_white_list()
        finally:
            zkOper.close()
            
        async_client = AsyncHTTPClient()
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
        finally:
            async_client.close()
        
        self.finish(server_cons_under_oom)
