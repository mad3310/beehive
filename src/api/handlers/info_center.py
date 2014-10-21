#!/usr/bin/env python
#-*- coding: utf-8 -*-

#import multiprocessing
import logging
from base import APIHandler
from common.serverOpers import Server_Opers

class InfoCenter(APIHandler):
    _logger = logging.getLogger("process_info")
   

#curl "http://localhost:8888/server"
    def get(self):
        server_oper = Server_Opers()
        info_set = server_oper.retrieve_host_stat()
        dict = {}
        self._logger.setLevel(logging.INFO)
        dict.setdefault("info_set", info_set)
        self.finish(dict)

#curl -d "container_name=/demo_centos" "http://localhost:8888/container/info"
    def post(self):
               
        args = self.request.arguments
        logging.info("args :" + str(args))
        for key in args:
            value = args[key][0]
        
        name = value
        container_server = Server_Opers(name)
        dict = {}
        container_resource = container_server.retrieve_container_stat()
        dict.setdefault("Container_resource", container_resource)
        self.finish(dict)
              
