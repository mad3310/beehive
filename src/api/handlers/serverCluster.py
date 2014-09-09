'''
Created on Sep 8, 2014

@author: root
'''
import uuid

from api.common.configFileOpers import ConfigFileOpers
from tornado.options import options
from api.handlers.base import APIHandler
from api.common.utils.exceptions import HTTPAPIError
from api.common.tornado_basic_auth import require_basic_auth

@require_basic_auth
class ServerClusterHandler(APIHandler):
    '''
    classdocs
    '''
    confOpers = ConfigFileOpers()

    # create server cluster
    # eg. curl --user root:root -d "clusterName=docker_cluster&dataNodeIp=10.200.91.153&dataNodeName=docker_cluster_node_1" "http://localhost:8888/serverCluster"
    def post(self):
        #check if exist cluster
        existCluster = self.zkOper.existCluster()
        if existCluster:
            raise HTTPAPIError(status_code=417, error_detail="server has belong to a cluster,should be not create new cluster!",\
                                notification = "direct", \
                                log_message= "server has belong to a cluster,should be not create new cluster!",\
                                response =  "the server has belonged to a cluster,should be not create new cluster!")
        
        requestParam = {}
        args = self.request.arguments
        for key in args:
            value = args[key][0]
            requestParam.setdefault(key,value)
            
        clusterUUID = str(uuid.uuid1())
        requestParam.setdefault("clusterUUID",clusterUUID)
        
        if requestParam != {}:
            self.confOpers.setValue(options.server_cluster_property, requestParam)
            self.confOpers.setValue(options.data_node_property, requestParam)
            
        clusterProps = self.confOpers.getValue(options.server_cluster_property)
        dataNodeProprs = self.confOpers.getValue(options.data_node_property)
        self.zkOper.writeClusterInfo(clusterUUID, clusterProps)
        self.zkOper.writeDataNodeInfo(clusterUUID, dataNodeProprs)
        
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
        
        