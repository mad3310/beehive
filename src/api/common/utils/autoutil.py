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