'''
Created on Sep 8, 2014

@author: root
'''
import uuid, json, logging

from common.configFileOpers import ConfigFileOpers
from common.serverOpers import Server_Opers
from common.utils.exceptions import HTTPAPIError
from common.tornado_basic_auth import require_basic_auth
from tornado.options import options
from handlers.base import APIHandler
from tornado.httpclient import HTTPRequest
from common.helper import _request_fetch
from common.ipOpers import IpOpers

@require_basic_auth
class ServerClusterHandler(APIHandler):
    '''
    classdocs
    '''
    confOpers = ConfigFileOpers()

    # create server cluster
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=192.168.84.132&dataNodeName=docker_cluster_node_1" "http://localhost:8888/serverCluster"
    def post(self):
        
        requestParam = self.get_all_arguments()
        existCluster = self.zkOper.existCluster()
        if existCluster:
            clusterUUID = self.zkOper.getClusterUUID()
        else:
            clusterUUID = str(uuid.uuid1())
            requestParam.setdefault("clusterUUID", clusterUUID)
        if requestParam != {}:
            self.confOpers.setValue(options.server_cluster_property, requestParam)
            self.confOpers.setValue(options.data_node_property, requestParam)
          
        clusterProps = self.confOpers.getValue(options.server_cluster_property)
        dataNodeProprs = self.confOpers.getValue(options.data_node_property)
        self.zkOper.writeClusterInfo(clusterUUID, clusterProps)
        self.zkOper.writeDataNodeInfo(clusterUUID, dataNodeProprs)

        dataNodeIp = requestParam.get('dataNodeIp')
        existDataNode = self.zkOper.existDataNode(clusterUUID, dataNodeIp)
        
        if existDataNode:
            raise HTTPAPIError(status_code=417, error_detail="DataNode has exist!",\
                                notification = "direct", \
                                log_message= "DataNode has been regedited!",\
                                response =  "This DataNode has been regedited!")
        
        dict = {}
        dict.setdefault("message", "creating server cluster successful!")
        self.finish(dict)
        
    def get(self):
        clusterUUID = self.zkOper.getClusterUUID()
        data, stat = self.zkOper.retrieveClusterProp(clusterUUID)
        self.confOpers.setValue(options.server_cluster_property, eval(data))
        
        dict = {}
        dict.setdefault("message", "sync server cluster info to local successful!")
        self.finish(dict)

@require_basic_auth
class GetServersInfoHandler(APIHandler):
    '''
    classdocs
    '''
    serverOpers = Server_Opers()
    
    
    def get(self):
        
        data_nodes_ip_list = self.zkOper.retrieve_data_node_list()
        url_post = "/server"
        resource_dict = {}
        for data_node_ip in data_nodes_ip_list:
            requesturi = "http://%s:%s%s" % (data_node_ip, options.port, url_post)
            request = HTTPRequest(url=requesturi, method='GET', connect_timeout=30.0, request_timeout=30.0)
            return_result = _request_fetch(request)
            retrun_dict = json.loads(return_result)
            resource_dict.setdefault(data_node_ip, retrun_dict['response'])
        
        self.finish(resource_dict)
        