#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import logging
import traceback

from base import APIHandler
from utils.exceptions import HTTPAPIError
from tornado_letv.tornado_basic_auth import require_basic_auth
from tornado.web import asynchronous
from container.containerOpers import Container_Opers, ContainerLoad
from componentProxy.componentDockerModelFactory import ComponentDockerModelFactory


@require_basic_auth
class ContainerHandler(APIHandler):
    
    container_opers = Container_Opers()
    component_docker_model_factory = ComponentDockerModelFactory()
    
    '''
    @todo: 
    1. should be modify to async way to issue this process and 
    2. check the create's process exception rethrow problem
    '''
    #@asynchronous
    def post(self):
        args = self.get_all_arguments()
        docker_model = self.__create_docker_module(args)
        self.container_opers.create(docker_model)
        return_message = {}
        return_message.setdefault("message", "Success Create Container")
        self.finish(return_message)

    def __create_docker_module(self, arg_dict):
        container_name = arg_dict.get('container_name')
        containerClusterName = arg_dict.get('containerClusterName')
        component_type = arg_dict.get('component_type')
        env = eval(arg_dict.get('env'))
        binds = eval(arg_dict.get('binds'))
        binds = self.__rewrite_bind_arg(component_type, containerClusterName, binds)
        logging.info('get create container args : %s, type:%s' % (str(arg_dict), type(arg_dict)) )
        docker_model = self.component_docker_model_factory.create(component_type, arg_dict)
        return docker_model

    def __rewrite_bind_arg(self, component_type, containerClusterName, bind_arg):
        re_bind_arg = {}
        for k,v in bind_arg.items():
            
            """
                need to make dir when '/data/mcluster_data' in bind path
            """
            
            if 'mclusternode' == component_type and '/data/mcluster_data' in k:
                _path = '/data/mcluster_data/d-mcl-%s' % containerClusterName
                if not os.path.exists(_path):
                    os.makedirs(_path)
                re_bind_arg.setdefault(_path, v)
            else:
                re_bind_arg.setdefault(k, v)
        return re_bind_arg

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

        self.container_opers.start(container_name)
        
        return_message = {}
        return_message.setdefault("message", "due to start a container need a little time, please wait and check the result~")
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
          

        self.container_opers.destroy(container_name)
          
        return_message = {}
        return_message.setdefault("message", "remove container has been done but need some time, please wait a moment and check the result!")
        self.finish(return_message)


@require_basic_auth
class GetherContainerMemeoyHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    def get(self, container_name):

        exists = self.container_opers.check_container_exists(container_name)
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
    
    container_opers = Container_Opers()
    
    @asynchronous
    def get(self, container_name):

        exists = self.container_opers.check_container_exists(container_name)
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
    
    container_opers = Container_Opers()
    
    def get(self, container_name):

        exists = self.container_opers.check_container_exists(container_name)
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
     
