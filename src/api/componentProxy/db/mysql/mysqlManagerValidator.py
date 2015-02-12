#-*- coding: utf-8 -*-

import time
import logging
from tornado.options import options
from utils.autoutil import http_get


class MclusterManagerValidator():
    
    def validate_manager_status(self, host_ip_list, container_model_list, num):
        
        logging.info('wait 5 seconds...')
        time.sleep(5)
         
        while num:
            stat = True
            succ = {}
            for index, host_ip in enumerate(host_ip_list):
                container_model = container_model_list[index]
                container_name = container_model.container_name
                logging.info('host_ip:%s, container_name:%s' % (host_ip, container_name) )
                ret = self.__get(container_name, host_ip)
                logging.info('check container %s,  result : %s' % (container_name, str(ret)))
                if ret:
                    succ.setdefault(host_ip, container_model)
                else:
                    stat = False
            logging.info('stat: %s' % str(stat))
            if stat:
                logging.info('successful!!!')
                return True
            
            for hostip, container_model in succ.items():
                container_model_list.remove(container_model)
                host_ip_list.remove(hostip)
            num -= 1
    
    def __get(self, containerName, container_node):
        ret = False
        url_post = "/inner/MclusterManager/status/%s" % containerName
        requesturi = "http://%s:%s%s" % (container_node, options.port, url_post)
        logging.debug('requesturi: %s' % requesturi)
        fetch_ret = http_get(requesturi)
        logging.info('fetch_ret:%s' % str(fetch_ret))
        ret = fetch_ret.get('response').get('message')
        logging.debug('fetch_ret.get response :%s' % type(fetch_ret.get('response')))
        logging.debug('get reslut: %s, type: %s' % ( str(ret), type(ret) ))
        return ret