#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster_handler import *
from handlers.server_handler import *
from handlers.containerCluster_handler import *
from handlers.container_handler import *
from handlers.monitor_handler import *
from handlers.ip import IPHandler
from handlers.port import PortHandler
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/admin/ips", IPHandler),
    (r"/admin/ports", PortHandler),
    
    ##'''  --------------------serverCluster-------------------------------
    
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/update", UpdateServerClusterHandler),
    (r"/serverCluster/containers/under_oom", SwitchServersUnderoomHandler),
    (r"/serverCluster/containers/disk", GetherServersContainersDiskLoadHandler),
    (r"/serverCluster/containers/memory/add", AddServersMemoryHandler),
    
    ##'''  --------------------server---------------------------------------'''
    
    (r"/server/resource", CollectServerResHandler),
    (r"/server/containers/memory/add", AddServerMemoryHandler),
    (r"/server/containers/under_oom", SwitchServerUnderoomHandler),
    (r"/server/containers/disk", GetherServerContainersDiskLoadHandler),
    (r"/inner/server/update", UpdateServerHandler),
    
    ##'''  --------------------containerCluster------------------------------'''
    
    (r"/containerCluster", ContainerClusterHandler),
    #(r"/containerCluster/(.*)", ContainerClusterHandler),
    (r"/containerCluster/start", ContainerClusterStartHandler),
    (r"/containerCluster/stop", ContainerClusterStopHandler),
    (r"/containerCluster/info", ContainerClustersInfoHandler),
    (r"/containerCluster/info/(.*)", ContainerClusterInfoHandler),
    (r"/containerCluster/sync", CheckClusterSyncHandler),
    (r"/containerCluster/createStatus/(.*)", CheckCreateClusterStatusHandler),
    (r"/containerCluster/status/(.*)", CheckContainerClusterStatusHandler),
    (r"/containerCluster/conf", ClusterConfigHandler),
    (r"/containerCluster/stat/(.*)/memory", GetherClusterMemeoyHandler),
    (r"/containerCluster/stat/(.*)/cpuacct", GetherClusterCpuacctHandler),
    (r"/containerCluster/stat/(.*)/networkio", GetherClusterNetworkioHandler),
    
    ##'''  --------------------container---------------------------------------'''
    
    (r"/inner/container", ContainerHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/remove", RemoveContainerHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
    (r"/container/stat/(.*)/memory", GetherContainerMemeoyHandler),
    (r"/container/stat/(.*)/cpuacct", GetherContainerCpuacctHandler),
    (r"/container/stat/(.*)/networkio", GetherContainerNetworkioHandler),
    (r"/container/manager/status", ManagerStatusHandler),
    
    ##'''  --------------------monitor--------------------------------------- '''
    
    (r"/monitor/status", ContainerStatus),
    (r"/monitor/serverCluster/containers/memory", CheckServersContainersMemLoad),
    (r"/monitor/serverCluster/containers/under_oom", CheckServersContainersUnderOom),
    (r"/inner/monitor/server/containers/memory", CheckServerContainersMemLoad),
    (r"/inner/monitor/server/containers/under_oom", CheckServerContainersUnderOom),
]
