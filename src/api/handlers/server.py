'''
Created on Sep 8, 2014

@author: root
'''
import traceback
import logging
import socket

from handlers.base import APIHandler
from common.serverOpers import Server_Opers
from common.resourceOpers import Res_Opers
from common.utils.exceptions import HTTPAPIError


class ServerHandler(APIHandler):
    '''
    classdocs
    '''
    server_opers = Server_Opers()

    def get(self):
        dict = self.server_opers.retrieveServerResource()
        return self.finish(dict)


class UpdateServerHandler(APIHandler):
    """
    update server container 
    """
    
    server_opers = Server_Opers()
    
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