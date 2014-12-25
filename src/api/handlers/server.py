'''
Created on Sep 8, 2014

@author: root
'''
import traceback
import logging
import socket
import re

from tornado.web import asynchronous
from handlers.base import APIHandler
from common.serverOpers import Server_Opers
from common.resourceOpers import Res_Opers
from common.utils.exceptions import HTTPAPIError
from common.tornado_basic_auth import require_basic_auth


class ServerHandler(APIHandler):
    '''
    classdocs
    '''
    server_opers = Server_Opers()

    @asynchronous
    def get(self):
        dict = self.server_opers.retrieveServerResource()
        return self.finish(dict)


class UpdateServerHandler(APIHandler):
    """
    update server container 
    """
    
    server_opers = Server_Opers()
    
    @asynchronous
    def get(self):
        try:
           self.server_opers.update()
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="update server failed!",\
                                notification = "direct", \
                                log_message= "update server failed!",\
                                response =  "update server failed!")
        dict = {}
        dict.setdefault("message", "update server successful")
        self.finish(dict)


class CollectServerResHandler(APIHandler):
    """
    update server container 
    """
    _logger = logging.getLogger("process_info")
    res_opers = Res_Opers()
    
    @asynchronous
    def get(self):
        
        try:
           server_res = self.res_opers.retrieve_host_stat()
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="get server resource failed!",\
                                notification = "direct", \
                                log_message= "get server resource failed!",\
                                response =  "please check!")
        
        self._logger.setLevel(logging.INFO)
        self.finish(server_res)


class CollectContainerResHandler(APIHandler):
    """
    update server container 
    """
    _logger = logging.getLogger("process_info")
    
    @asynchronous
    def get(self):
        
        try:
            res_opers = Res_Opers()
            container_res = res_opers.retrieve_container_stat()
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="get container resource failed!",\
                                notification = "direct", \
                                log_message= "get container resource failed!",\
                                response =  "please check!")
        
        self._logger.setLevel(logging.INFO)
        self.finish(container_res)


class AddServerMemoryHandler(APIHandler): pass


@require_basic_auth
class SwitchServerUnderoomHandler(APIHandler):

    server_opers = Server_Opers()

    def post(self):
        args = self.get_all_arguments()
        switch = args.get('switch')
        
        if not switch or (switch!='on' and switch!='off'):
            raise HTTPAPIError(status_code=400, error_detail="switch params wrong!",\
                                notification = "direct", \
                                log_message= "switch params wrong!",\
                                response =  "please check params!")
        
        containerNameList = args.get('containerNameList')
        if not containerNameList:
            raise HTTPAPIError(status_code=400, error_detail="containerNameList params not given!",\
                                notification = "direct", \
                                log_message= "containerNameList params not given!",\
                                response =  "please check params!")
        
        if ',' in containerNameList:
            containerNameList = containerNameList.split(',')
        else:
            containerNameList = [containerNameList]
        
        value, result = 0, {}
        try:
            if switch == 'on':
                result = self.server_opers.open_containers_under_oom(containerNameList)
            elif switch == 'off':
                result = self.server_opers.shut_containers_under_oom(containerNameList)
        except:
            logging.error( str(traceback.format_exc()) )
        
        logging.info('under_oom result: %s' % str(result))   
        self.finish(result)


@require_basic_auth
class GetherServerContainersDiskLoadHandler(APIHandler):
    """get the disk container use server 
    
    """
    
    server_opers = Server_Opers()
    
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        container_name_list = containers.split(',')
        if not (container_name_list and isinstance(container_name_list, list)):
            raise HTTPAPIError(status_code=400, error_detail="containerNameList is illegal!",\
                                notification = "direct", \
                                log_message= "containerNameList is illegal!",\
                                response =  "please check params!")
        
        host_ip = self.request.remote_ip
        container_disk_load = {}
        try:
            container_disk_load = self.server_opers.get_containers_disk_load(container_name_list)
        except:
            logging.error( str( traceback.format_exc() ) )
            raise HTTPAPIError(status_code=500, error_detail="server exceptions",\
                                notification = "direct", \
                                log_message= "server exception",\
                                response =  "server exception!")
        
        logging.info('get disk load on this server:%s, result:%s' %( host_ip, str(container_disk_load)) )
        self.finish(container_disk_load)
        
        
