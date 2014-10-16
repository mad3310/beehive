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

def _init_container(containerName=None):
    timeout = 5
    get_route_cmd = r"route -n|grep -w 'UG'"
    if containerName is None:
        return False
    try:
        c = docker.Client('unix://var/run/docker.sock')
        re_info = c.inspect_container(containerName)
        for env in re_info['Config']['Env']:
            if re.match(r"^IP=", env):
                key, ip = re.split(r"=", env)
            if re.match(r"^NETMASK=", env):
                key, mask = re.split(r"=", env)
        real_route = ''
        for i in range(0,4):
            if i != 3:
                real_route = real_route + str(int(ip.split(r".")[i])&int(mask.split(r".")[i])) + r"."
            else:
                real_route = real_route + str((int(ip.split(r".")[i])&int(mask.split(r".")[i]))+1)
        child = pexpect.spawn(r"docker attach %s" % (containerName))
        child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
        child.sendline(get_route_cmd)
        child.expect(['0.0.0.0.*bash', pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
        if child.after == pexpect.TIMEOUT:
            route_list = []
        else:
            route_list = child.after.replace('bash','').split("\r\n")
        r_list = _get_route_dicts(route_list)
        if r_list is False:
            return False
        if len(r_list) > 0:
            for route in r_list:
                if route['route_ip'] == real_route:
                    continue
                else:
                    child.sendline(r"route del -net 0.0.0.0/%s gw %s dev %s" % (route['mask_num'], route['route_ip'], route['dev']))
                    child.expect(["bash", pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
        child.sendline(get_route_cmd)
        child.expect(['0.0.0.0.*bash', pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
        if child.after == pexpect.TIMEOUT:
            route_list = []
        else:
            route_list = child.after.replace("bash",'').split("\r\n")
        r_list = _get_route_dicts(route_list)
        if r_list is False:
            return False
        if len(r_list) == 0:
            child.sendline(r"route add default gw %s" % (real_route))
            child.expect(["#", pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
            child.sendline(r"")
            child.close()
        elif len(r_list) > 1 or r_list[0]['route_ip'] != real_route:
            return False
    except Exception, e:
        logging.error(e)
        raise e
    return True

def _get_route_dicts(route_list=None):
    if route_list is None:
        return False
    r_list = []
    for line in route_list:
        if ( line == '' ): continue
        route_info = {}
        route_info['route_ip'] = line.split()[1]
        mask_num = _mask_to_num(line.split()[2])
        if type(mask_num) is dict:
            logging.error('netmask Illegal: %s' % (mask_num['false']))
            return False
        else:
            route_info['mask_num'] = mask_num
        route_info['dev'] = line.split()[7]
        r_list.append(route_info)
    return r_list

def _mask_to_num(netmask=None):
    if netmask is None:
        return { 'false': netmask }
    num = ''
    for i in range(0,4):
        ip = int(netmask.split(r".")[i])
        if ip > 255 or ip < 0:
            return { 'false': netmask }
        num = num + str(bin(ip).replace('0b',''))
    return len(num.replace(r"0",''))