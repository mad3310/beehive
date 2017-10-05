#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging

from base import APIHandler
from utils.exceptions import HTTPAPIError
from tornado_letv.tornado_basic_auth import require_basic_auth
from tornado.web import asynchronous
from container.containerOpers import Container_Opers
from componentProxy.componentDockerModelFactory import ComponentDockerModelFactory
from status.status_enum import Status


@require_basic_auth
class ContainerHandler(APIHandler):
    
    container_opers = Container_Opers()
    component_docker_model_factory = ComponentDockerModelFactory()

    #@asynchronous
    def post(self):
        args = self.get_all_arguments()
        docker_model = self.__create_docker_module(args)
        self.container_opers.create(docker_model)
        return_message = {}
        return_message.setdefault("message", "Success Create Container")
        self.finish(return_message)

    def __create_docker_module(self, arg_dict):
        logging.info('get create container args : %s, type:%s' % (str(arg_dict), type(arg_dict)) )
        docker_model = self.component_docker_model_factory.create(arg_dict)
        return docker_model


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
        if stat == Status.started:
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
        if stat == Status.stopped:
            massage = {}
            massage.setdefault("status", stat)
            massage.setdefault("message", "no need this operation, the container has been stopped!")
            self.finish(massage)
            return
        
        self.container_opers.stop(container_name)
        
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
class SetContainerCpusharesHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        ret = self.container_opers.set_container_cpushares(args)
        
        self.finish(ret)


@require_basic_auth
class SetContainerCpusetHandler(APIHandler):
    
    container_opers = Container_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        ret = self.container_opers.set_container_cpuset(args)
        
        result = {}
        result.setdefault(ret)
        self.finish(result)


@require_basic_auth
class CheckContainerStatusHandler(APIHandler):
    '''
    classdocs
    '''
    container_opers = Container_Opers()
    
    @asynchronous
    def get(self, container_name):
        status = self.container_opers.check(container_name)
        self.finish(status)



class ManagerStatusHandler(APIHandler):

    container_opers = Container_Opers()
    
    @asynchronous
    def post(self):
        """
            eg. curl --user root:root -d  "containerName=d-mcl-zz2-n-3&componentType=mcluster" /container/manager/status
        """
        args = self.get_all_arguments()
        container_name = args.get('containerName')
        component_type = args.get('componentType')
        if not (container_name and component_type):
            raise HTTPAPIError(status_code=417, error_detail="no containerName or componentType argument!",\
                                notification = "direct", \
                                log_message= "no containerName or componentType argument!",\
                                response =  "please check params!")
        
        ret = self.container_opers.manager_status_validate(component_type, container_name)
        
        result = {}
        result.setdefault("message", ret)
        self.finish(result)
