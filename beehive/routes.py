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
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/sync", SyncServerClusterHandler),

    ##'''  --------------------server---------------------------------------'''
    (r"/server/containers/memory/add", AddServerMemoryHandler),
    (r"/server/containers/under_oom", SwitchServerUnderoomHandler),
    (r"/server/containers/disk/bps", SetServerContainersDiskBpsHandler),
    (r"/server/containers/disk/iops", SetServerContainersDiskIopsHandler),
    (r"/inner/server/sync", SyncServerHandler),
    (r"/server/image/pull", PullImageToServerHandler),

    ##'''  --------------------containerCluster------------------------------'''

    (r"/containerCluster", ContainerClusterHandler),
    (r"/containerCluster/start", ContainerClusterStartHandler),
    (r"/containerCluster/stop", ContainerClusterStopHandler),
    (r"/containerCluster/sync", CheckClusterSyncHandler),      #need to remove to container-monitor-agent
    (r"/containerCluster/status/(.*)", CheckContainerClusterStatusHandler),
    (r"/containerCluster/createResult/(.*)", CheckContainerClusterCreateResultHandler),
    (r"/containerCluster/node", ContainerClusterNodeHandler),
    (r"/containerCluster/(.*)/node/(.*)", ContainerClusterNodeHandler),
    (r"/containerCluster/node/remove", ContainerClusterRemoveNodeHandler),
    (r"/containerCluster/conf", ClusterConfigHandler),
    (r"/containerCluster/cpushares", SetContainerClusterCpusharesHandler),
    (r"/containerCluster/containers/under_oom", SwitchServersUnderoomHandler),
    (r"/containerCluster/containers/memory/add", AddServersMemoryHandler),
    ##'''  --------------------container---------------------------------------'''

    (r"/inner/container", ContainerHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/remove", RemoveContainerHandler),
    (r"/container/cpushares", SetContainerCpusharesHandler),
    #(r"/container/cpuset", SetContainerCpusetHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
    (r"/container/manager/status", ManagerStatusHandler),

    ##'''  --------------------monitor--------------------------------------- '''

    (r"/monitor/status", ContainerStatus),     #need to remove to container-monitor-agent

    ##'''  --------------------resource--------------------------------------- '''
    (r"/resource/ip", FetchIpHandler),
]
