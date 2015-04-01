#-*- coding: utf-8 -*-
import os
import stat
import base64
import shutil

from utils.configFileOpers import ConfigFileOpers
from base import APIHandler
from tornado.options import options


# admin conf
# eg. curl -d "zkAddress=10.204.8.211" "http://localhost:8888/admin/conf"
class AdminConf(APIHandler):
    
    confOpers = ConfigFileOpers()
    
    def post(self):
        requestParam = {}
        args = self.request.arguments
        for key in args:
            requestParam.setdefault(key,args[key][0])
            
        if requestParam != {}:
            self.confOpers.setValue(options.container_manager_property, requestParam)
        
        return_message = {}
        return_message.setdefault("message", "admin conf successful!")
        self.finish(return_message)
        
# admin reset
# eg. curl --user root:root "http://localhost:8888/admin/reset"
class AdminReset(APIHandler):
    
    def get(self):
        template_path=os.path.join(options.base_dir, "templates")
        config_path = os.path.join(options.base_dir, "config")
        
        clusterPropTemFileName = os.path.join(template_path,"serverCluster.property.template")
        dataNodePropTemFileName = os.path.join(template_path,"dataNode.property.template")
        mclusterManagerCnfTemFileName = os.path.join(template_path,"containerManager.property.template")
        
        clusterPropFileName = os.path.join(config_path,"serverCluster.property")
        dataNodePropFileName = os.path.join(config_path,"dataNode.property")
        mclusterManagerCnfFileName = os.path.join(config_path,"containerManager.property")
        fileNameList = [clusterPropFileName,dataNodePropFileName,mclusterManagerCnfFileName]
        
        for fileName in fileNameList:
            if os.path.exists(fileName):
                os.chmod(fileName, stat.S_IWRITE)
                os.remove(fileName)
            
        shutil.copyfile(clusterPropTemFileName, clusterPropFileName)
        shutil.copyfile(dataNodePropTemFileName, dataNodePropFileName)
        shutil.copyfile(mclusterManagerCnfTemFileName, mclusterManagerCnfFileName)
        
        return_message = {}
        return_message.setdefault("message", "admin reset successful!")
        self.finish(return_message)


# create admin user
# eg. curl -d "adminUser=root&adminPassword=root" "http://localhost:8888/admin/user"
class AdminUser(APIHandler):
    
    confOpers = ConfigFileOpers()
    
    def post(self):
        requestParam = {}
        args = self.request.arguments
        for key in args:
            value = args[key][0]
            if key == 'adminPassword':
                value = base64.encodestring(value).strip('\n')
            requestParam.setdefault(key,value)
            
        if requestParam != {}:
            self.confOpers.setValue(options.server_cluster_property, requestParam)
        
        return_message = {}
        return_message.setdefault("message", "creating admin user successful!")
        self.finish(return_message)