#!/usr/bin/env python 2.6.6

from utils.autoutil import *
from dockerOpers import Docker_Opers


class Container():
    def __init__(self, container=None, inspect={}, inspect_file=None):
        self.inspect = {}
        if not self.inspect:
            self.init_inspect(container, inspect, inspect_file)

    def init_inspect(self, container=None, inspect={}, inspect_file=None):
        if container:
            docker_opers = Docker_Opers()
            self.inspect =  docker_opers.inspect_container(container)
        elif inspect:
            self.inspect = inspect
        else:
            pass
        
    def memory(self):
        return self.inspect.get('Config').get('Memory')
    
    def volumes(self):
        return self.inspect.get('Volumes')

    def cluster(self, container):
        return get_containerClusterName_from_containerName(container)

    def zookeeper_id(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if 'ZKID' in item:
                return self._get_value(item)

    def ip(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('IP'):
                return self._get_value(item)
        
    def gateway(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('GATEWAY'):
                return self._get_value(item)

    def netmask(self):
        Env = self.inspect.get('Config').get('Env')
        for item in Env:
            if item.startswith('NETMASK'):
                return self._get_value(item)
    
    def _get_value(self, item):
        try:
            value = re.findall('.*=(.*)', item)[0]
            return value
        except:
            logging.error( str(traceback.format_exc()) )

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
