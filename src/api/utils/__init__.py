#-*- coding: utf-8 -*-

import random
import string
import base64
import logging
import re, traceback
import datetime
import urllib
import time
import json
import os

from tornado.options import options
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPError
from utils.configFileOpers import ConfigFileOpers
from tornado.gen import engine, Task
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from utils.exceptions import CommonException

confOpers = ConfigFileOpers()

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_random_password():
    a = list(string.letters+string.digits)
    random.shuffle(a)
    random.shuffle(a)
    random.shuffle(a)
    return "".join(a[:8])

def _is_ip(ip=None):
    if ip is None:
        return False
    pattern = r"\b(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[1-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\b"
    if re.match(pattern, ip) is None:
        return False
    return True

def _is_mask(mask=None):
    if mask is None:
        return False
    pattern = r"\b(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\b"
    if re.match(pattern, mask) is None:
        return False
    return True

def _request_fetch(request):
    #access to the target ip machine to retrieve the dict,then modify the config
    http_client = HTTPClient()
    
    response = None
    try:
        response = http_client.fetch(request)
    finally:
        http_client.close()
    
    return_result = False
    if response is None:
        raise CommonException('response is None!')
    
    if response.error:
        return_result = False
        message = "remote access,the key:%s,error message:%s" % (request,response.error)
        logging.error(message)
    else:
        return_result = response.body.strip()
            
    return return_result
    
def _retrieve_userName_passwd():
    confDict = confOpers.getValue(options.server_cluster_property, ['adminUser','adminPassword'])
    adminUser = confDict['adminUser']
    adminPasswd = base64.decodestring(confDict['adminPassword'])
    return (adminUser, adminPasswd)

def getDictFromText(sourceText, keyList):
    totalDict = {}
    resultValue = {}
    
    lineList = sourceText.split('\n')
    for line in lineList:
        if not line:
            continue
        
        pos1 = line.find('=')
        key = line[:pos1]
        value = line[pos1+1:len(line)].strip('\n')
        totalDict.setdefault(key,value)
        
    if keyList == None:
        resultValue = totalDict
    else:
        for key in keyList:
            value = totalDict.get(key)
            resultValue.setdefault(key,value)
            
    return resultValue

def _mask_to_num(netmask=None):
    if netmask is None:
        return { 'false': netmask }
    num = ''
    if not _is_mask(netmask):
        return { 'false': netmask }
    for i in range(0,4):
        ip = int(netmask.split(r".")[i])
        if ip > 255 or ip < 0:
            return { 'false': netmask }
        num = num + str(bin(ip).replace('0b',''))
    return len(num.replace(r"0",''))
    
def _get_gateway_from_ip(ip):
    ip_item_list = ip.split('.')
    ip_item_list[-1] = '1'
    ip_item_list[-2] = '0'
    return '.'.join(ip_item_list)
    
def get_current_time():
    dt = datetime.datetime.now()
    return dt.strftime(TIME_FORMAT)

def _get_property_dict(class_model_obj):
    """use this method temporarily, later add to class Container_Model
    
    """
    result = {}
    for _property, value in class_model_obj.__dict__.items():
        __property = _property[1:]
        result.setdefault(__property, value)
    return result

def __isExcept(e, eType = Exception):
    return isinstance(e, eType)

def handleTimeout(func, timeout, *params, **kwargs):
    
    interval = 0.6
    if type(timeout) == tuple:
        timeout, interval = timeout
        
    rst = None
    while timeout > 0:
        t = time.time()
        rst = func(*params, **kwargs)
        if rst and not __isExcept(rst):
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

def ping_ip_available(ip):
    cmd = 'ping -w 1 %s' % str(ip)
    ping_ret = os.system(cmd)
    if ping_ret == 0:
        return True
    
    return False

def nc_ip_port_available(host_ip, port):
    cmd = 'nc -z -w1 %s %s' % (host_ip, port)
    _nc_ret = os.system(cmd)
    if _nc_ret != 0:
        return False
    return True

def http_post(url, body={}, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):
    request = HTTPRequest(url=url, method='POST', body=urllib.urlencode(body), connect_timeout=_connect_timeout, \
                          request_timeout=_request_timeout, auth_username = auth_username, auth_password = auth_password)
    fetch_ret = _request_fetch(request)
    return_dict = json.loads(fetch_ret)
    logging.info('POST result :%s' % str(return_dict))
    return return_dict

def http_get(url, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):   
    request = HTTPRequest(url=url, method='GET', connect_timeout=_connect_timeout, request_timeout=_request_timeout,\
                          auth_username = auth_username, auth_password = auth_password)
    fetch_ret = _request_fetch(request)
    return_dict = json.loads(fetch_ret)
    logging.info('GET result :%s' % str(return_dict))
    return return_dict
    

@engine
def async_http_post(url, body={}, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):
    async_client = AsyncHTTPClient()
    try:
        request = HTTPRequest(url=url, method='POST', body=urllib.urlencode(body), connect_timeout=_connect_timeout, \
                              request_timeout=_request_timeout, auth_username = auth_username, auth_password = auth_password)
        response = yield Task(async_client.fetch, request)
        return_dict = json.loads( response.body.strip())
        logging.info('POST result :%s' % str(return_dict))
    finally:
        async_client.close()

def get_containerClusterName_from_containerName(container_name):
    containerClusterName = ''
    if 'd-' in container_name:
        containerClusterName = re.findall('d-\w{3,}-(.*)-n-\d', container_name)[0]
    elif 'd_mcl' in container_name:
        containerClusterName = re.findall('d_mcl_(.*)_node_\d', container_name)[0]
    elif 'vip' in container_name:
        containerClusterName = re.findall('d-vip-(.*)', container_name)[0]
    elif 'doc-mcl' in container_name:
        containerClusterName = re.findall('doc-mcl-(.*)-n-\d', container_name)[0]
    else:
        containerClusterName = container_name
    return containerClusterName
