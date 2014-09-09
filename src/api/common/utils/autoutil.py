#!/usr/bin/env python
#-*- coding: utf-8 -*-

import httplib, urllib
import socket, time

def _isExcept(e, eType = Exception):
    return isinstance(e, eType)

def handleTimeout(func, timeout, *params, **paramMap):
    """
    一段时间内做某件事情, 有结果退出, 没有结果或者异常继续尝试
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

def doHttpGet(uri, headers = {}):
    """
    http的get请求
    """
    
    return _doHttp(uri, 'GET', None, headers)

def doHttpPost(uri, body, headers = {}):
    """
    http的post请求
    """
    
    return _doHttp(uri, 'POST', body, headers)

def getHost():
    """
    获取机器的ip地址
    """
    
    return socket.gethostbyname(socket.gethostname())

def __parseUri(uri):
    """
    从uri中分离出host和location
    """
    
    index1 = uri.find('://') + 3
    index2 = uri.find('/', index1)
    if index2 == -1:
        return uri[index1:], '/'
    return uri[index1:index2], uri[index2:]

def _tryExcept(func, *params, **paramMap):
    try:
        return func(*params, **paramMap)
    except Exception, e:
        return e

def _doHttp(uri, method, body, headers = {}):
    host, location = __parseUri(uri)
    baseHeaders = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'GBK,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': host,
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7'
    }
    if headers:
        for k, v in headers.items():
            baseHeaders[k] = v
    conn = None
    try:
        conn = httplib.HTTPConnection(host)
        conn.request(method, location, body, headers)
        res = conn.getresponse()
        headers = {}
        for k, v in res.getheaders():
            headers[k] = v
        return res.status, headers, res.read()
    except Exception, e:
        return e
    finally:
        if conn:
            _tryExcept(conn.close)

def doPost(url, body):
    data = urllib.urlencode(body)
    rst = urllib.urlopen(url, data)
    return rst.read()

if __name__ == '__main__':
    #env = {'ZKID':'1', 'IP':'10.160.145.106', 'HOSTNAME':'docker-m-n-2', 'NETMASK':'255.255.0.0',
           #'GATEWAY':'10.160.0.1', 'N1_IP':'10.160.145.105', 'N1_HOSTNAME':'docker-m-n-1', 'N2_IP':'10.160.145.106',
           #'N2_HOSTNAME':'docker-m-n-2', 'N3_IP':'10.160.145.107', 'N3_HOSTNAME':'docker-m-n-3'}
    
    #body = {'hasIP' : True,
         #'container_1_args' : {'hostIP':'192.168.1.106', 'ipAddr':'10.160.145.105', 'containerName':'test-m-1', 'zookeeperId':'1', 'geteAddr':'10.160.0.1', 'netMark':'255.255.0.0'},
         #'container_2_args':{'hostIP':'192.168.1.106', 'ipAddr':'10.160.145.106', 'containerName':'test-m-2', 'zookeeperId':'2', 'geteAddr':'10.160.0.1', 'netMark':'255.255.0.0'},
         #'container_3_args':{'hostIP':'192.168.1.106', 'ipAddr':'10.160.145.107', 'containerName':'test-m-3', 'zookeeperId':'3', 'geteAddr':'10.160.0.1', 'netMark':'255.255.0.0'}
         #}
    #print doPost('http://192.168.1.106:8080/dealVIP', body)
    
    body = {'containerName': 'test-m-3', 'zookeeperId': '3', 'n3_ip': '10.160.145.107', 
     'ipAddr': '10.160.145.107', 'netMark': '255.255.0.0', 'n2_ip': '10.160.145.106', 
     'geteAddr': '10.160.0.1', 'hostIP': '192.168.1.106', 'n3_hostname': 'test-m-3', 
     'n1_ip': '10.160.145.105', 'n1_hostname': 'test-m-1', 'n2_hostname': 'test-m-2'}
    url = 'http://192.168.1.106:8080/mclusterContainer'
    print doPost(url, body)