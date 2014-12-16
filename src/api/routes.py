#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster import *
from handlers.server import *
from handlers.containerCluster import *
from handlers.container import *
from handlers.monitor import *
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/update", UpdateServerClusterHandler),
    (r"/serverCluster/resource", GetServersInfoHandler),
    (r"/server", ServerHandler),
    (r"/server/resource", CollectServerResHandler),
    (r"/server/containers/resource", CollectContainerResHandler),
    (r"/inner/server/update", UpdateServerHandler),
    (r"/containerCluster", ContainerClusterHandler),
    #(r"/containerCluster/(.*)", ContainerClusterHandler),
    (r"/containerCluster/start", ContainerClusterStartHandler),
    (r"/containerCluster/stop", ContainerClusterStopHandler),
    (r"/containerCluster/info", ContainerClustersInfoHandler),
    (r"/containerCluster/info/(.*)", ContainerClusterInfoHandler),
    (r"/containerCluster/sync", CheckClusterSyncHandler),
    (r"/containerCluster/createStatus/(.*)", CheckCreateClusterStatusHandler),
    (r"/containerCluster/status/(.*)", CheckContainerClusterStatusHandler),
    (r"/containerCluster/resource/disk/([.*])", GatherContainersDiskLoadHandler),
    (r"/inner/MclusterManager/status/(.*)", StartMclusterManagerHandler),
    (r"/containerCluster/conf", ClusterConfigHandler),
    (r"/containerCluster/ips/add", AddIpsIntoIpPoolHandler),
    (r"/inner/container", ContainerHandler),
    (r"/container/resource/disk/([.*])", GetContainersDiskLoadHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/remove", RemoveContainerHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
    (r"/monitor/status", ContainerStatus),
    #(r"/containerCluster/ips/get", GetIpsFromIpPool),
    
]
