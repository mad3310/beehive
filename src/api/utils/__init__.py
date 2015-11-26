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
from utils.configFileOpers import ConfigFileOpers
from tornado.gen import engine, Task
from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPClient, HTTPError
from utils.exceptions import CommonException
from tornado.gen import Callback, Wait

confOpers = ConfigFileOpers()

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_zk_address():
    ret_dict = confOpers.getValue(options.container_manager_property, ['zkAddress','zkPort'])
    zk_address = ret_dict['zkAddress']
    zk_port = ret_dict['zkPort']
    return zk_address, zk_port

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

def _set_dict_property(args_dict, cls):
    cls_obj = cls
    for key, value in args_dict.items():
        _key = '_' + key
        cls_obj.__setattr__(_key, value)
    return cls_obj

def has_property(class_model_obj, _property):
    _property = '_' + _property
    return _property in class_model_obj.__dict__

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

def getNIC():
    content = os.popen('route -n').read()
    matched_items = re.findall('.*UG(\s+\d+){3}\s+(\w+)', content)
    return matched_items[-1][-1]

def getHostIp():
    NIC = getNIC()
    cmd = "ifconfig %s|grep 'inet addr'|awk '{print $2}'" % NIC
    out_ip = os.popen(cmd).read()
    ip = out_ip.split('\n')[0]
    ip = re.findall('.*:(.*)', ip)[0]
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
def async_http_post(async_client, url, body={}, _connect_timeout=40.0, _request_timeout=40.0, auth_username=None, auth_password=None):
    request = HTTPRequest(url=url, method='POST', body=urllib.urlencode(body), connect_timeout=_connect_timeout, \
                          request_timeout=_request_timeout, auth_username = auth_username, auth_password = auth_password)
    yield Task(async_client.fetch, request)


'''
    This method below only dispatch task, not validate result actually.
'''
@engine
def dispatch_mutil_task(request_ip_port_params_list, uri, http_method):
    http_client = AsyncHTTPClient()
    _error_record_dict = {}
    adminUser, adminPasswd = _retrieve_userName_passwd()
    try:
        _key_sets = set()
        for (req_ip, req_port, params) in request_ip_port_params_list:
            requesturl = "http://%s:%s%s" % (req_ip, req_port, uri)
            logging.info('requesturi: %s' % requesturl)
            logging.info('dispatch mutil task params :%s' % str(params))
            request = HTTPRequest(url=requesturl, method=http_method, body=urllib.urlencode(params), \
                                  connect_timeout=40, request_timeout=40, auth_username=adminUser, auth_password=adminPasswd)
            
            callback_key = "%s_%s_%s" % (uri, req_ip, req_port)
            _key_sets.add(callback_key)
            http_client.fetch(request, callback=(yield Callback(callback_key)))
        
        for callback_key in _key_sets:
            response = yield Wait(callback_key)
            
            if response.error:
                return_result = False
                error_record_msg = "remote access,the key:%s,error message:%s" % (callback_key,response.error)
            else:
                return_result = response.body.strip()
            
            if cmp('false', return_result) == 0:
                callback_key_ip = callback_key.split("_")[-1]
                _error_record_dict.setdefault(callback_key_ip, error_record_msg)

        if len(_error_record_dict) > 0:
            raise CommonException('request occurs error! detail: %s' % str(_error_record_dict))
        else:
            logging.info('request finished all!')
                
    finally:
        http_client.close()

def get_containerClusterName_from_containerName(container_name):
    containerClusterName = ''
    if re.match('^d-mcl.*n-4', container_name):
        containerClusterName = re.findall('d-\w{3,}-(.*)-n-\d', container_name)[0]
        containerClusterName = '%s_vip' % containerClusterName
    elif 'd-vip' in container_name:
        containerClusterName = re.findall('d-vip-(.*)', container_name)[0]
        containerClusterName = '%s_vip' % containerClusterName
    elif 'd-' in container_name:
        containerClusterName = re.findall('d-\w{3,}-(.*)-n-\d', container_name)[0]
    elif 'd_mcl' in container_name:
        containerClusterName = re.findall('d_mcl_(.*)_node_\d', container_name)[0]
    elif 'doc-mcl' in container_name:
        containerClusterName = re.findall('doc-mcl-(.*)-n-\d', container_name)[0]
    else:
        containerClusterName = container_name
    return containerClusterName


def get_file_data(file_path, mode='r'):
    with open(file_path, mode) as f:
        data = f.read()
        f.close()
    return data


def get_dev_number_by_mount_dir(mount_dir):
    content = get_file_data('/etc/fstab')
    device_path = re.findall('(\/dev.*?)\s+%s' % mount_dir, content)[0]
    device_path = os.path.realpath(device_path)
    
    parent_device = device_path.split('/')[-1]
    
    if not parent_device.startswith('dm'):
        parent_device = re.sub('\d+', '', parent_device)
    
    dev_num_path = r'/sys/class/block/%s/dev'  % parent_device
    dev_num = get_file_data(dev_num_path)
    return dev_num.strip()
