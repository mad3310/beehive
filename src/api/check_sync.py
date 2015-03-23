#!/usr/bin/env python2.6.6

import logging
import json

from zk.zkOpers import ZkOpers
from utils.configFileOpers import ConfigFileOpers
from utils.autoutil import getHostIp
from tornado.options import options


class CheckSync():
    
    zkOpers = ZkOpers()
    config_file_obj = ConfigFileOpers()

    '''
        cluster will not  be existed,
        when the first to start container-manager in a new server cluster
         
    '''
    
    def sync(self):
        if self.zkOpers.existCluster():
            self.sync_server_cluster()
            self.sync_data_node()
        else:
            logging.info("cluster does not exist, may be the first time to sync in a new server cluster")

    def sync_server_cluster(self):
        cluster_uuid = self.zkOpers.getClusterUUID() 
        uuid_value, stat = self.zkOpers.retrieveClusterProp(cluster_uuid) 
        uuid_value = uuid_value.replace("'", "\"")
        uuid_value = json.loads(uuid_value)
        self.config_file_obj.setValue(options.server_cluster_property, uuid_value) 


    def sync_data_node(self):
        server_ip = getHostIp()
        server_ip_list = self.zkOpers.retrieve_data_node_list()
        if server_ip in server_ip_list:
            logging.info('')
            data_node_value = self.zkOpers.retrieve_data_node_info(server_ip)
            if isinstance(data_node_value, dict):
                self.config_file_obj.setValue(options.data_node_property, data_node_value)
        else:
            logging.error('server %s should be registered first' % str(server_ip) )