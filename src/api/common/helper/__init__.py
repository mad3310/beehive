import base64
import logging
import docker
import re, traceback
import pexpect

from tornado.options import options
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPError
from common.configFileOpers import ConfigFileOpers

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

def init_container(containerName=None):
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
        if not is_ip(ip):
            logging.error("get IP error: %s" % ip)
            return False
        if not is_mask(mask):
            logging.error("get MASK error: %s" % mask)
            return False
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
        if isinstance(r_list, dict):
            if r_list.has_key('false'):
                logging.error(r_list['false'])
            else:
                logging.error('unknow error: %s' % (str(r_list)))
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
        logging.info("route_list: %s" % str(route_list))
        r_list = _get_route_dicts(route_list)
        if isinstance(r_list, dict):
            if r_list.has_key('false'):
                logging.error(r_list['false'])
            else:
                logging.error('unknow error: %s' % (str(r_list)))
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

def is_ip(ip=None):
    if ip is None:
        return False
    pattern = r"\b(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[1-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\b"
    if re.match(pattern, ip) is None:
        return False
    return True

def is_mask(mask=None):
    if mask is None:
        return False
    pattern = r"\b(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9]{0,2}|[1-9][0-9]|[0-9])\b"
    if re.match(pattern, mask) is None:
        return False
    return True

def _get_route_dicts(route_list=None):
    if route_list is None:
        return { 'false': 'route_list is None' }
    r_list = []
    for line in route_list:
        if ( line == '' ): continue
        route_ip = line.split()[1]
        netmask = line.split()[2]
        if ( len(route_ip.split(r'.')) != 4 or len(netmask.split(r'.')) !=4 ): continue
        route_info = {}
        route_info['route_ip'] = route_ip
        mask_num = _mask_to_num(netmask)
        if isinstance(mask_num, dict):
            return { 'false' : 'netmask Illegal: %s' % (mask_num['false']) }
        else:
            route_info['mask_num'] = mask_num
        route_info['dev'] = line.split()[7]
        if not route_info in r_list:  
            r_list.append(route_info)
    return r_list

def _mask_to_num(netmask=None):
    if netmask is None:
        return { 'false': netmask }
    num = ''
    if not is_mask(netmask):
        return { 'false': netmask }
    for i in range(0,4):
        ip = int(netmask.split(r".")[i])
        if ip > 255 or ip < 0:
            return { 'false': netmask }
        num = num + str(bin(ip).replace('0b',''))
    return len(num.replace(r"0",''))

def get_container_stat(container_name):
    """
    """
    
    exists = check_container_exists(container_name)
    if not exists:
        return 'destroyed'
    c = docker.Client('unix://var/run/docker.sock')
    container_info_list =  c.containers(all=True)
    for container_info in container_info_list:
        name = container_info.get('Names')[0]
        name = name.replace('/', '')
        if name == container_name:
            stat = container_info.get('Status')
            if 'Up' in stat:
                return 'started'
            elif 'Exited' in stat:
                return 'stopped'

def get_all_containers():
    container_name_list = []
    c = docker.Client('unix://var/run/docker.sock')
    container_info_list = c.containers(all=True)
    flag = False
    for container_info in container_info_list:
        name = container_info.get('Names')[0]
        name = name.replace('/', '')
        container_name_list.append(name)
    return container_name_list

def check_container_exists(container_name):
    container_name_list = []
    container_name_list = get_all_containers()
    return container_name in container_name_list

# def check_container_exists(container_name):
#     c = docker.Client('unix://var/run/docker.sock')
#     container_info_list = c.containers(all=True)
#     flag = False
#     for container_info in container_info_list:
#         name = container_info.get('Names')[0]
#         name = name.replace('/', '')
#         logging.info('name:%s; container_name:%s' %(name, container_name))
#         if name == container_name:
#             flag = True
#             break
#     return flag
