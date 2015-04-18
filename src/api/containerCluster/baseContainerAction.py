'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys

from tornado.options import options
from tornado.httpclient import AsyncHTTPClient
from common.abstractAsyncThread import Abstract_Async_Thread
from utils import _retrieve_userName_passwd
from utils import async_http_post
from zk.zkOpers import ZkOpers



class ContainerCluster_Action_Base(Abstract_Async_Thread):

    def __init__(self, containerClusterName, action):
        super(ContainerCluster_Action_Base, self).__init__()
        self.cluster = containerClusterName
        self.action = action

    def run(self):
        try:
            self.__issue_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def __issue_action(self):
        params = self.__get_params()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        logging.info('params: %s' % str(params))
        
        async_client = AsyncHTTPClient()
        try:
            for host_ip, container_name_list in params.items():
                logging.info('container_name_list %s in host %s ' % (str(container_name_list), host_ip) )
                for container_name in container_name_list:
                    args = {'containerName':container_name}
                    request_uri = 'http://%s:%s/container/%s' % (host_ip, options.port, self.action)
                    logging.info('post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
                    async_http_post(async_client, request_uri, body=args, auth_username=adminUser, auth_password=adminPasswd)
        finally:
            async_client.close()
        
        if self.action == 'remove':
            self.__do_when_remove_cluster()

    def __do_when_remove_cluster(self):
        zkOper = ZkOpers()
        try:
            cluster_info = zkOper.retrieve_container_cluster_info(self.cluster)
            use_ip = cluster_info.get('isUseIp')
            if use_ip:
                container_ip_list = zkOper.retrieve_container_list(self.cluster)
                logging.info('container_ip_list:%s' % str(container_ip_list) )
                zkOper.recover_ips_to_pool(container_ip_list)
        finally:
            zkOper.close()

    def __get_params(self):
        """
            two containers may be with a host_ip
        """
        
        params, container_info = {}, {}
        
        zkOper = ZkOpers()
        
        try:
            container_ip_list = zkOper.retrieve_container_list(self.cluster)
        
            for contaier_ip in container_ip_list:
                container_name_list = []
                container_info = zkOper.retrieve_container_node_value(self.cluster, contaier_ip)
                container_name = container_info.get('containerName')
                host_ip = container_info.get('hostIp')
                container_name_list.append(container_name)
                params[host_ip] = container_name_list
        finally:
            zkOper.close()
        
        return params
        