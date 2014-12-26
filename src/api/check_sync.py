#!/usr/bin/env python2.6.6

from common.zkOpers import ZkOpers
from common.configFileOpers import ConfigFileOpers


class CheckSync():
    
    zkOpers = ZkOpers('127.0.0.1', 2181)
    config_file_obj = ConfigFileOpers()

    def sync(self):
        if self.zkOpers.existCluster():
            self.sync_server_cluster()
            self.sync_data_node()
        else:
             logging.info("cluster does not exist")

    def sync_server_cluster(self):
        cluster_uuid = self.zkOpers.getClusterUUID() 
        uuid_value = self.zkOpers.retrieveClusterProp(cluster_uuid) 
        
        if isinstance(uuid_value, dict):
            self.config_file_obj.setValue(options.server_cluster_property, uuid_value) 
        else:
            logging.error("sync server cluster property info failed!")

    def sync_data_node(self):
        server_ip = socket.gethostbyname(socket.gethostname())
        server_ip_list = self.zkOpers.retrieve_data_node_list()
        if server_ip in server_ip_list:
            logging.info('')
            data_node_value = self.zkOpers.retrieve_data_node_info(server_ip)
            if isinstance(data_node_value, dict):
                self.config_file_obj.setValue(options.data_node_property, data_node_value)
        else:
            logging.error('sync data node failed')