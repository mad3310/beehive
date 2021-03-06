#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re

from dockerForBeehive.dockerOpers import Docker_Opers 

class ImageOpers(object):
    
    def __init__(self):
        '''
        constructor
        '''
    
    docker_opers = Docker_Opers()
    
    def pull(self, image):
        self.docker_opers.pull(image)
        return self.image_exist(image)

    def check_image_name_legal(self, image):
        image_pattern= '((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)\:\d+.*'
        matched = re.match(image_pattern, image)
        return matched is not None

    def image_exist(self, image):
        image_list = self.docker_opers.image_name_list()
        return image in image_list
