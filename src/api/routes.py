#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster_handler import *
from handlers.server_handler import *
from handlers.containerCluster_handler import *
from handlers.container_handler import *
from handlers.monitor_handler import *
from handlers.ip import IPHandler, FetchIpHandler
from handlers.port import PortHandler
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/admin/ips", IPHandler),
    (r"/admin/ports", PortHandler),
    
    ##'''  --------------------serverCluster-------------------------------
#     '''
#     @todo: why many of under_oom link? what mean?
#     '''
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/update", UpdateServerClusterHandler),
    (r"/serverCluster/containers/under_oom", SwitchServersUnderoomHandler),
    (r"/serverCluster/containers/disk", GatherServersContainersDiskLoadHandler),
    (r"/serverCluster/containers/memory/add", AddServersMemoryHandler),
    
    ##'''  --------------------server---------------------------------------'''
    (r"/server/resource", CollectServerResHandler),
    (r"/server/containers/memory/add", AddServerMemoryHandler),
    (r"/server/containers/under_oom", SwitchServerUnderoomHandler),
    (r"/server/containers/disk", GatherServerContainersDiskLoadHandler),
    (r"/server/containers/disk/bps", SetServerContainersDiskBpsHandler),
    (r"/server/containers/disk/iops", SetServerContainersDiskIopsHandler),
    (r"/inner/server/update", UpdateServerHandler),
    
    ##'''  --------------------containerCluster------------------------------'''
    
    (r"/containerCluster", ContainerClusterHandler),
    (r"/containerCluster/start", ContainerClusterStartHandler),
    (r"/containerCluster/stop", ContainerClusterStopHandler),
    (r"/containerCluster/sync", CheckClusterSyncHandler),
    (r"/containerCluster/status/(.*)", CheckContainerClusterStatusHandler),
    (r"/containerCluster/createResult/(.*)", CheckContainerClusterCreateResultHandler),
    (r"/containerCluster/node", ContainerClusterNodeHandler),
    (r"/containerCluster/(.*)/node/(.*)", ContainerClusterNodeHandler),
    (r"/containerCluster/node/remove", ContainerClusterRemoveNodeHandler),
    
#     '''
#     @todo: used below uri?
#     '''
    (r"/containerCluster/conf", ClusterConfigHandler),
    (r"/containerCluster/cpushares", SetContainerClusterCpusharesHandler),
    (r"/containerCluster/stat/(.*)/memory", GatherClusterMemeoyHandler),
    (r"/containerCluster/stat/(.*)/cpuacct", GatherClusterCpuacctHandler),
    (r"/containerCluster/stat/(.*)/networkio", GatherClusterNetworkioHandler),
    (r"/containerCluster/stat/(.*)/disk", GatherClusterDiskHandler),
    
    ##'''  --------------------container---------------------------------------'''
    
    (r"/inner/container", ContainerHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/remove", RemoveContainerHandler),
    (r"/container/cpushares", SetContainerCpusharesHandler),
    #(r"/container/cpuset", SetContainerCpusetHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
    (r"/container/stat/(.*)/memory", GatherContainerMemeoyHandler),
    (r"/container/stat/(.*)/cpuacct", GatherContainerCpuacctHandler),
    (r"/container/stat/(.*)/networkio", GatherContainerNetworkioHandler),
    
#     '''
#     @todo: need to add /inner for this uri
#     '''
    (r"/container/manager/status", ManagerStatusHandler),
    
    ##'''  --------------------monitor--------------------------------------- '''
    
    (r"/monitor/status", ContainerStatus),
    
    ##'''  --------------------resource--------------------------------------- '''
    (r"/resource/ip", FetchIpHandler),
]
