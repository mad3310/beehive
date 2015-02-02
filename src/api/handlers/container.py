#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging
import traceback

from base import APIHandler
from common.containerOpers import *
from common.serverOpers import *
from common.utils.exceptions import HTTPAPIError
from common.tornado_basic_auth import require_basic_auth
from common.helper import *
from tornado.web import asynchronous


@require_basic_auth
class ContainerHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        create_failed_rst = self.container_opers.issue_create_action(args)
        if create_failed_rst:
            logging.error('container %s create failed' % create_failed_rst)
            raise HTTPAPIError(status_code=417, error_detail="container created failed!",\
                                notification = "direct", \
                                log_message= "container created failed!",\
                                response =  "container created failed!")
        dict = {}
        dict.setdefault("message", "Success Create Container")
        self.finish(dict)
        
#     def delete(self, container_name):
# #         args = self.get_all_arguments()
# #         container_name = args.get('containerName')
#         logging.info('container_name: %s' % container_name)
#         exists = check_container_exists(container_name)
#         if not exists:
#             massage = {}
#             massage.setdefault("status", "not exist")
#             massage.setdefault("message", "no need this operation, there is no such a container!")
#             self.finish(massage)
#             return
#         
#         try:
#             logging.info( container_name )
#             self.container_opers.destroy(container_name)
#         except:
#             logging.error( str(traceback.format_exc()) )
#             raise HTTPAPIError(status_code=500, error_detail="container start raise exception!",\
#                                 notification = "direct", \
#                                 log_message= "container start raise exception",\
#                                 response =  "container start raise exception, please check!!")
#          
#         dict = {}
#         dict.setdefault("message", "remove container has been done but need some time, please wait a little and check the result!")
#         self.finish(dict)

@require_basic_auth
class StartContainerHandler(APIHandler):
     
    container_opers = Container_Opers()
    
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        logging.info('all_arguments: %s' % str(args))
        
        container_name = args.get('containerName')
        if not container_name:
            raise HTTPAPIError(status_code=400, error_detail="no container_name argument!",\
                                notification = "direct", \
                                log_message= "no container_name argument!",\
                                response =  "please check params!")
        
        exists = check_container_exists(container_name)
        if not exists:
            raise HTTPAPIError(status_code=400, error_detail="container %s not exist!" % container_name,\
                                notification = "direct", \
                                log_message= "container %s not exist!" % container_name,\
                                response =  "please check!")
        
        stat = get_container_stat(container_name)
        if stat == 'started':
            massage = {}
            massage.setdefault("status", stat)
            massage.setdefault("message", "no need this operation, the container has been started!")
            self.finish(massage)
            return
        
        try: 
            self.container_opers.start(container_name)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="container start raise exception!",\
                                notification = "direct", \
                                log_message= "container start raise exception",\
                                response =  "container start raise exception, please check!!")
        
        massage = {}
        massage.setdefault("message", "due to start a container need a little time, please wait and check the result~")
        self.finish(massage)


@require_basic_auth
class StopContainerHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        logging.info('all_arguments: %s' % str(args))
        container_name = args.get('containerName')
        if not container_name:
            raise HTTPAPIError(status_code=400, error_detail="no container_name argument!",\
                                notification = "direct", \
                                log_message= "no container_name argument!",\
                                response =  "please check params!")
        
        exists = check_container_exists(container_name)
        if not exists:
            raise HTTPAPIError(status_code=400, error_detail="container %s not exist!" % container_name,\
                                notification = "direct", \
                                log_message= "container %s not exist!" % container_name,\
                                response =  "please check!")
        
        stat = get_container_stat(container_name)
        if stat == 'stopped':
            massage = {}
            massage.setdefault("status", stat)
            massage.setdefault("message", "no need this operation, the container has been stopped!")
            self.finish(massage)
            return
        
        try: 
            self.container_opers.stop(container_name)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="container stop raise exception!",\
                                notification = "direct", \
                                log_message= "container stop raise exception",\
                                response =  "container stop raise exception, please check!!")
        
        massage = {}
        massage.setdefault("message", "due to stop a container need a little time, please wait and check the result~")
        self.finish(massage)


@require_basic_auth
class RemoveContainerHandler(APIHandler):
        
    container_opers = Container_Opers()
    
    @asynchronous    
    def post(self):
        args = self.get_all_arguments()
        logging.info('all_arguments: %s' % str(args))
        container_name = args.get('containerName')
        if not container_name:
            raise HTTPAPIError(status_code=400, error_detail="no container_name argument!",\
                                notification = "direct", \
                                log_message= "no container_name argument!",\
                                response =  "please check params!")            
        
        exists = check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("status", "not exist")
            massage.setdefault("message", "no need this operation, there is no such a container!")
            self.finish(massage)
            return
          
        try:
            logging.info( container_name )
            self.container_opers.destroy(container_name)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="container start raise exception!",\
                                notification = "direct", \
                                log_message= "container start raise exception",\
                                response =  "container start raise exception, please check!!")
          
        dict = {}
        dict.setdefault("message", "remove container has been done but need some time, please wait a little and check the result!")
        self.finish(dict)


@require_basic_auth
class GetherContainerMemeoyHandler(APIHandler):
    
    @asynchronous
    def get(self, container_name):

        exists = check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("message", "container %s not exists" % container_name)
            self.finish(massage)
            return

        result, memory_stat_item = {}, {}
        conl = ContainerLoad(container_name)
        memory_stat_item = conl.get_memory_stat_item()
        current_time = get_current_time()
        
        result.setdefault('memory', memory_stat_item)
        result.setdefault('time', current_time)
        result.setdefault('containerName', container_name)
        self.finish(result)


@require_basic_auth
class GetherContainerCpuacctHandler(APIHandler):
    
    @asynchronous
    def get(self, container_name):

        exists = check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("message", "container %s not exists" % container_name)
            self.finish(massage)
            return

        result, cpuacct_stat_item = {}, {}
        conl = ContainerLoad(container_name)
        cpuacct_stat_item = conl.get_cpuacct_stat_item()
        current_time = get_current_time()
        
        result.setdefault('cpuacct', cpuacct_stat_item)
        result.setdefault('time', current_time)
        result.setdefault('containerName', container_name)
        self.finish(result)


@require_basic_auth
class GetherContainerNetworkioHandler(APIHandler):
    
    def get(self, container_name):

        exists = check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("message", "container %s not exists" % container_name)
            self.finish(massage)
            return

        result, network_io_item = {}, {}
        conl = ContainerLoad(container_name)
        network_io_item = conl.get_network_io()
        current_time = get_current_time()
        
        result.setdefault('networkio', network_io_item)
        result.setdefault('time', current_time)
        result.setdefault('containerName', container_name)
        self.finish(result)


@require_basic_auth
class CheckContainerStatusHandler(APIHandler):
    '''
    classdocs
    '''
    container_opers = Container_Opers()
    
    @asynchronous
    def get(self, container_name):
        
        exists = check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("status", "not exist")
            massage.setdefault("message", "")
            self.finish(massage)
            return
          
        try:
            status = self.container_opers.check(container_name)
        except:
            logging.error(str( traceback.format_exc() ))
            raise HTTPAPIError(status_code=578, error_detail="check method exception!",\
                                notification = "direct", \
                                log_message= "check method exception",\
                                response =  "check method failed!")
        
        self.finish(status)
     
