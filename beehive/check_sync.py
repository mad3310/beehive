#!/usr/bin/env python2.6.6

import logging
import json

from zk.zkOpers import Common_ZkOpers
from utils.configFileOpers import ConfigFileOpers
from utils import getHostIp, get_zk_address
from tornado.options import options


class CheckSync():
    
    config_file_obj = ConfigFileOpers()

    '''
        cluster will not  be existed,
        when the first to start container-manager in a new server cluster
         
    '''
    
    def sync(self):
        zk_address, zk_port = get_zk_address()
        if not (zk_address and zk_port):
            logging.info('admin zookeeper first!')
            return
        
        zkOper = Common_ZkOpers()

        existed = zkOper.existCluster()
        if existed:
            self._sync_server_cluster()
            self._sync_data_node()
        else:
            logging.info("cluster does not exist, may be the first time to sync in a new server cluster")

    def _sync_server_cluster(self):
        zkOper = Common_ZkOpers()
        cluster_uuid = zkOper.getClusterUUID() 
        uuid_value, _ = zkOper.retrieveClusterProp(cluster_uuid) 

        uuid_value = uuid_value.replace("'", "\"")
        uuid_value = json.loads(uuid_value)
        self.config_file_obj.setValue(options.server_cluster_property, uuid_value) 

    def _sync_data_node(self):
        server_ip = getHostIp()
        
        zkOper = Common_ZkOpers()
        server_ip_list = zkOper.retrieve_data_node_list()
        if server_ip in server_ip_list:
            data_node_value = zkOper.retrieve_data_node_info(server_ip)
            if isinstance(data_node_value, dict):
                self.config_file_obj.setValue(options.data_node_property, data_node_value)
        else:
            logging.error('server %s should be registered first' % str(server_ip) )
