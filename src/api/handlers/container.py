#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging
import traceback

from base import APIHandler
from utils.exceptions import HTTPAPIError
from tornado.tornado_basic_auth import require_basic_auth
from tornado.web import asynchronous
from container.containerOpers import Container_Opers


@require_basic_auth
class ContainerHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    '''
    @todo: 
    1. should be modify to async way to issue this process and 
    2. check the create's process exception rethrow problem
    '''
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        try:
            self.container_opers.create(args)
        except:
            raise HTTPAPIError(status_code=500, error_detail="container created failed!",\
                                notification = "direct", \
                                log_message= "container created failed!",\
                                response =  "container created failed!")
            
        return_message = {}
        return_message.setdefault("message", "Success Create Container")
        self.finish(return_message)
        
#     def delete(self, container_name):
# #         args = self.get_all_arguments()
# #         container_name = args.get('containerName')
#         logging.info('container_name: %s' % container_name)
#         exists = self.container_opers.check_container_exists(container_name)
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
#             raise HTTPAPIError(status_code=500, error_detail="container __start raise exception!",\
#                                 notification = "direct", \
#                                 log_message= "container __start raise exception",\
#                                 response =  "container __start raise exception, please check!!")
#          
#         dict = {}
#         dict.setdefault("message", "remove container has been done but need some time, please wait a moment and check the result!")
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
            raise HTTPAPIError(status_code=417, error_detail="no container_name argument!",\
                                notification = "direct", \
                                log_message= "no container_name argument!",\
                                response =  "please check params!")
        
        exists = self.container_opers.check_container_exists(container_name)
        if not exists:
            raise HTTPAPIError(status_code=417, error_detail="container %s not exist!" % container_name,\
                                notification = "direct", \
                                log_message= "container %s not exist!" % container_name,\
                                response =  "please check!")
        
        stat = self.container_opers.get_container_stat(container_name)
        if stat == 'started':
            massage = {}
            massage.setdefault("status", stat)
            massage.setdefault("message", "no need this operation, the container has been started!")
            self.finish(massage)
            return
        
        try: 
            self.container_opers.__start(container_name)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="container __start raise exception!",\
                                notification = "direct", \
                                log_message= "container __start raise exception",\
                                response =  "container __start raise exception, please check!!")
        
        return_message = {}
        return_message.setdefault("message", "due to __start a container need a little time, please wait and check the result~")
        self.finish(return_message)


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
        
        exists = self.container_opers.check_container_exists(container_name)
        if not exists:
            raise HTTPAPIError(status_code=400, error_detail="container %s not exist!" % container_name,\
                                notification = "direct", \
                                log_message= "container %s not exist!" % container_name,\
                                response =  "please check!")
        
        stat = self.container_opers.get_container_stat(container_name)
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
        
        return_message = {}
        return_message.setdefault("message", "due to stop a container need a little time, please wait and check the result~")
        self.finish(return_message)


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
        
        exists = self.container_opers.check_container_exists(container_name)
        if not exists:
            massage = {}
            massage.setdefault("status", "not exist")
            massage.setdefault("message", "no need this operation, there is no such a container!")
            self.finish(massage)
            return
          
        try:
            self.container_opers.destroy(container_name)
        except:
            logging.error( str(traceback.format_exc()) )
            raise HTTPAPIError(status_code=500, error_detail="container __start raise exception!",\
                                notification = "direct", \
                                log_message= "container __start raise exception",\
                                response =  "container __start raise exception, please check!!")
          
        return_message = {}
        return_message.setdefault("message", "remove container has been done but need some time, please wait a moment and check the result!")
        self.finish(return_message)


@require_basic_auth
class CheckContainerStatusHandler(APIHandler):
    '''
    classdocs
    '''
    container_opers = Container_Opers()
    
    @asynchronous
    def get(self, container_name):
        
        exists = self.container_opers.check_container_exists(container_name)
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
     
