import base64
import logging
import docker
import re, traceback

from tornado.options import options
from common.configFileOpers import ConfigFileOpers
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPError

confOpers = ConfigFileOpers()

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

def get_container_stat(container_name):
    """
    0: started
    1: stoped
    2: deleted or not exist
    """
    
    exists = check_container_exists(container_name)
    if not exists:
        return 2
    c = docker.Client('unix://var/run/docker.sock')
    container_info_list =  c.containers(all=True)
    for container_info in container_info_list:
        name = container_info.get('Names')[0]
        name = name.replace('/', '')
        if name == container_name:
            stat = container_info.get('Status')
            if 'Up' in stat:
                return 0
            elif 'Exited' in stat:
                return 1

def check_container_exists(container_name):
    c = docker.Client('unix://var/run/docker.sock')
    container_info_list = c.containers(all=True)
    flag = False
    for container_info in container_info_list:
        name = container_info.get('Names')[0]
        name = name.replace('/', '')
        if name == container_name:
            flag = True
    return flag
    