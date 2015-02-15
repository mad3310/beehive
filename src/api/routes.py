#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster_handler import *
from handlers.server_handler import *
from handlers.containerCluster_handler import *
from handlers.container_handler import *
from handlers.monitor_handler import *
from handlers.ip import *
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/admin/ips", IPHandler),
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/update", UpdateServerClusterHandler),
    (r"/serverCluster/resource", GetServersInfoHandler),
    (r"/serverCluster/containers/under_oom", SwitchServersUnderoomHandler),
    (r"/serverCluster/containers/disk", GetherServersContainersDiskLoadHandler),
    (r"/serverCluster/containers/memory/add", AddServersMemoryHandler),
    (r"/server", ServerHandler),
    (r"/server/resource", CollectServerResHandler),
    (r"/server/containers/resource", CollectContainerResHandler),
    (r"/server/containers/memory/add", AddServerMemoryHandler),
    (r"/server/containers/under_oom", SwitchServerUnderoomHandler),
    (r"/server/containers/disk", GetherServerContainersDiskLoadHandler),
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
    (r"/containerCluster/conf", ClusterConfigHandler),

    (r"/containerCluster/ips/add", AddIpsIntoIpPoolHandler),
    '''
    @todo: need to un-comment
    '''
    #(r"/containerCluster/ips/get", GetIpsFromIpPool),
    (r"/containerCluster/stat/(.*)/memory", GetherClusterMemeoyHandler),
    (r"/containerCluster/stat/(.*)/cpuacct", GetherClusterCpuacctHandler),
    (r"/containerCluster/stat/(.*)/networkio", GetherClusterNetworkioHandler),
    (r"/inner/container", ContainerHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/remove", RemoveContainerHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
    (r"/container/stat/(.*)/memory", GetherContainerMemeoyHandler),
    (r"/container/stat/(.*)/cpuacct", GetherContainerCpuacctHandler),
    (r"/container/stat/(.*)/networkio", GetherContainerNetworkioHandler),
    (r"/inner/MclusterManager/status/(.*)", StartMclusterManagerHandler),
    (r"/monitor/status", ContainerStatus),
    (r"/monitor/serverCluster/containers/memory", CheckServersContainersMemLoad),
    (r"/monitor/serverCluster/containers/under_oom", CheckServersContainersUnderOom),
    (r"/monitor/server/containers/memory", CheckServerContainersMemLoad),
    (r"/monitor/server/containers/under_oom", CheckServerContainersUnderOom),
]
