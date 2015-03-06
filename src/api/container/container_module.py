#!/usr/bin/env python 2.6.6
import re

from utils.autoutil import *


class Container():
    def __init__(self, inspect={}):
        if inspect:
            self.inspect = inspect

    def memory(self):
        return self.inspect.get('Config').get('Memory')

    def volumes(self):
        return self.inspect.get('Volumes')

    def cluster(self, container_name):
        return get_containerClusterName_from_containerName(container_name)

    def zookeeper_id(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if 'ZKID' in item:
                return self.__get_value(item)

    def ip(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('IP'):
                return self.__get_value(item)
        
    def gateway(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('GATEWAY'):
                return self.__get_value(item)

    def netmask(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('NETMASK'):
                return self.__get_value(item)

    def __get_value(self, item):
        return re.findall('.*=(.*)', item)[0]

    def image(self):
        return self.inspect.get('Config').get('Image')

    def type(self):
        image = self.image()
        if 'gbalancer' in image:
            return 'mclustervip'
        else:
            return 'mclusternode'

    def name(self):
        name = self.inspect.get('Name')
        if name:
            return name.replace('/', '')

    def hostname(self):
        return self.inspect.get('Config').get('Hostname')

    def id(self):
        return self.inspect.get('Id')

    def create_info(self, container_node_value):
        create_info = {}
        if isinstance(container_node_value, dict):
            self.inspect = container_node_value.get('inspect')
            create_info.setdefault('hostIp', container_node_value.get('hostIp') )
            create_info.setdefault('type', container_node_value.get('type') )
            container_name = self.name()
            create_info.setdefault('containerClusterName', self.cluster(container_name) )
            create_info.setdefault('zookeeperId', self.zookeeper_id() )
            create_info.setdefault('gateAddr', self.gateway() )
            create_info.setdefault('netMask', self.netmask() )
            create_info.setdefault('mountDir', str(self.volumes()) )
            create_info.setdefault('ipAddr', self.ip() )
            create_info.setdefault('containerName', self.name() )
        return create_info    
