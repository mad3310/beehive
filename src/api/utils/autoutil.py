#!/usr/bin/env python
#-*- coding: utf-8 -*-

import urllib
import time
import logging
import traceback
import threading
import json
import os, re

from tornado.httpclient import HTTPRequest
from utils import _request_fetch

class FuncThread(threading.Thread):
    def __init__(self, func, *params, **paramMap):
        threading.Thread.__init__(self)
        self.func = func
        self.params = params
        self.paramMap = paramMap
        self.rst = None
        self.finished = False

    def run(self):
        self.rst = self.func(*self.params, **self.paramMap)
        self.finished = True

    def getResult(self):
        return self.rst

    def isFinished(self):
        return self.finished

'''
@todo: the class used?
'''
class Data:
    def __init__(self, data = None):
        self.data = data

    def get(self):
        return self.data

    def set(self, data):
        self.data = data

def doInThread(func, *params, **paramMap):
    ft = FuncThread(func, *params, **paramMap)
    ft.start()
    return ft

'''
@todo: the method used?
'''
def doInTimes(func, times, *params, **paramMap):
    while times > 0:
        rst = func(*params, **paramMap)
        if rst and not isExcept(rst):
            break
        times = times - 1
    return rst

def _isExcept(e, eType = Exception):
    return isinstance(e, eType)

'''
@todo: the method used?
'''
def handleTimeout(func, timeout, *params, **paramMap):
    """
    """
    
    interval = 0.6
    if type(timeout) == tuple:
        timeout, interval = timeout
    rst = None
    while timeout > 0:
        t = time.time()
        rst = func(*params, **paramMap)
        if rst and not _isExcept(rst):
            break
        time.sleep(interval)
        timeout -= time.time() - t
    return rst

def getHostIp():
    out_ip = os.popen("ifconfig $(route -n|grep UG|awk '{print $NF}')|grep 'inet addr'|awk '{print $2}'").read()
    ip = out_ip.split('\n')[0]
    ip = re.findall('.*:(.*)', ip)[0]
    logging.info("host ip: %s" % (ip))
    return ip

'''
@todo: the method used?
'''
def getVMIp():
    ips = os.popen("/sbin/ifconfig | grep 'inet addr' | awk '{print $2}'").read()
    ip = ips.split('\n')[1]
    ip = re.findall('.*:(.*)', ip)[0]
    return ip

def ping_ip_able(ip):
    cmd = 'ping -w 1 %s' % str(ip)
    ping_ret = os.system(cmd)
    if ping_ret == 0:
        return True
    
    return False
    
def nc_ip_port_available(host_ip, port):
    cmd = 'nc -z -W1 %s %s' % (host_ip, port)
    _nc_ret = os.system(cmd)
    if _nc_ret is None or _nc_ret == '':
        return False
    
    return True

def http_post(url, body={}, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):
    try:
        request = HTTPRequest(url=url, method='POST', body=urllib.urlencode(body), connect_timeout=_connect_timeout, \
                              request_timeout=_request_timeout, auth_username = auth_username, auth_password = auth_password)
        fetch_ret = _request_fetch(request)
        return_dict = json.loads(fetch_ret)
        logging.info('POST result :%s' % str(return_dict))
        return return_dict
    except Exception, e:
        logging.error(str(e))
        return e

def http_get(url, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):   
    try:
        request = HTTPRequest(url=url, method='GET', connect_timeout=_connect_timeout, request_timeout=_request_timeout,\
                              auth_username = auth_username, auth_password = auth_password)
        fetch_ret = _request_fetch(request)
        return_dict = json.loads(fetch_ret)
        logging.info('GET result :%s' % str(return_dict))
        return return_dict
    except Exception, e:
        logging.error(str(e))
        return e
    
def get_containerClusterName_from_containerName(container_name):
    containerClusterName = ''
    if 'd-mcl' in container_name:
        containerClusterName = re.findall('d-mcl-(.*)-n-\d', container_name)[0]
    elif 'd_mcl' in container_name:
        containerClusterName = re.findall('d_mcl_(.*)_node_\d', container_name)[0]
    elif 'vip' in container_name:
        containerClusterName = re.findall('d-vip-(.*)', container_name)[0]
    elif 'doc-mcl' in container_name:
        containerClusterName = re.findall('doc-mcl-(.*)-n-\d', container_name)[0]
    else:
        containerClusterName = container_name
    return containerClusterName
