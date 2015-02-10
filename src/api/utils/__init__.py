#-*- coding: utf-8 -*-

import random
import string
import base64
import logging
import re, traceback
import datetime

from tornado.options import options
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPError
from utils.configFileOpers import ConfigFileOpers

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
    except HTTPError, e:
        logging.error(e)
    
    return_result = False
    if response != None:    
        if response.error:
            return_result = False
            message = "remote access,the key:%s,error message:%s" % (request,response.error)
            logging.error(message)
        else:
            return_result = response.body.strip()
            
    http_client.close()
            
    return return_result
    
def _retrieve_userName_passwd():
    confDict = confOpers.getValue(options.server_cluster_property, ['adminUser','adminPassword'])
    adminUser = confDict['adminUser']
    adminPasswd = base64.decodestring(confDict['adminPassword'])
    return (adminUser,adminPasswd)

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
        property = _property.replace('_', '')
        result.setdefault(property, value)
    return result
