#-*- coding: utf-8 -*-

import logging

from tornado.options import options
from utils.autoutil import http_get


class NginxManagerValidator(object):
    
    def __init__(self, container_model_list):
        self.container_model_list = container_model_list

    def validate_manager_status(self, container_model_list, num):
        
        while num:
            stat = True
            succ = []
            for index, container_model in enumerate(container_model_list):
                host_ip = container_model.host_ip
                container_name = container_model.container_name
                logging.info('host_ip:%s, container_name:%s' % (host_ip, container_name) )
                ret = self.__get(container_name, host_ip)
                logging.info('check container %s,  result : %s' % (container_name, str(ret)))
                if ret:
                    succ.append(container_model)
                else:
                    stat = False
            logging.info('stat: %s' % str(stat))
            if stat:
                logging.info('successful!!!')
                return True
            
            for container_model in succ:
                container_model_list.remove(container_model)
            num -= 1

    def __get(self, containerName, container_node):
        url_post = "/inner/nginxManager/status/%s" % containerName
        requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
        logging.info('requesturi: %s' % requesturi)
        fetch_ret = http_get(requesturi)
        logging.info('fetch_ret:%s' % str(fetch_ret))
        ret = fetch_ret.get('response').get('message')
        logging.info('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
        logging.info('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
        return ret