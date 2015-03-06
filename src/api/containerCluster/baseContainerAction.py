'''
Created on 2015-2-2

@author: asus
'''
import logging
import sys

from tornado.options import options
from common.abstractAsyncThread import Abstract_Async_Thread
from utils import _retrieve_userName_passwd
from utils.autoutil import async_http_post


class ContainerCluster_Action_Base(Abstract_Async_Thread):

    def __init__(self, containerClusterName, action):
        super(ContainerCluster_Action_Base, self).__init__()
        self.cluster = containerClusterName
        self.action = action

    def run(self):
        try:
            logging.info('do cluster %s ' % self.action)
            self._issue_action()
        except:
            self.threading_exception_queue.put(sys.exc_info())

    def _issue_action(self):
        params = self.get_params()
        adminUser, adminPasswd = _retrieve_userName_passwd()
        self.dispatch_container_tasks(params, adminUser, adminPasswd)

    def dispatch_container_tasks(self, params, admin_user, admin_passwd):
        logging.info('params: %s' % str(params))
        for host_ip, container_name_list in params.items():
            logging.info('container_name_list %s in host %s ' % (str(container_name_list), host_ip) )
            for container_name in container_name_list:
                self.post(host_ip, container_name, admin_user, admin_passwd)
        
        if self.action == 'remove':
            container_ip_list = self.zkOper.retrieve_container_list(self.cluster)
            logging.info('container_ip_list:%s' % str(container_ip_list) )
            self.zkOper.recover_ips_to_pool(container_ip_list)

    def post(self, host_ip, container_name, admin_user, admin_passwd):
        args = {}
        args.setdefault('containerName', container_name)
        request_uri = 'http://%s:%s/container/%s' % (host_ip, options.port, self.action)
        logging.info('post-----  url: %s, \n body: %s' % ( request_uri, str (args) ) )
        async_http_post(request_uri, body=args, auth_username=admin_user, auth_password=admin_passwd)

    def get_params(self):
        """
            two containers may be with a host_ip
        """
        
        params, container_info = {}, {}
        
        container_ip_list = self.zkOper.retrieve_container_list(self.cluster)
        
        for contaier_ip in container_ip_list:
            container_name_list = []
            container_info = self.zkOper.retrieve_container_node_value(self.cluster, contaier_ip)
            container_name = container_info.get('containerName')
            host_ip = container_info.get('hostIp')
            container_name_list.append(container_name)
            params[host_ip] = container_name_list
        return params
        