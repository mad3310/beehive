#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging

from base import APIHandler
from common.containerOpers import Container_Opers
from common.utils.exceptions import HTTPAPIError
from common.tornado_basic_auth import require_basic_auth

@require_basic_auth
class ContainerHandler(APIHandler):
    
    containerOpers = Container_Opers()
    
    def post(self):
        args = self.get_all_arguments()
        logging.info('all_arguments: %s' % str(args))

        create_rst = self.containerOpers.issue_create_action(args)
        
        if create_rst:
            raise HTTPAPIError(status_code=417, error_detail="container created failed!",\
                                notification = "direct", \
                                log_message= "container created failed!",\
                                response =  "container created failed!")
        
        dict = {}
        dict.setdefault("message", "Success Create Container")
        
        self.finish(dict)