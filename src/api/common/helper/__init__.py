import base64
import logging

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
