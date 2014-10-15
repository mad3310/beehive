#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster import *
from handlers.server import ServerHandler
from handlers.containerCluster import *
from handlers.container import *
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/serverCluster", ServerClusterHandler),
    (r"/serverCluster/resources", GetServersInfoHandler),
    (r"/server", ServerHandler),
    (r"/containerCluster", ContainerClusterHandler),
    (r"/containerCluster/conf", ClusterConfigHandler),
    (r"/containerCluster/ips", AddIpsIntoIpPoolHandler),
    (r"/containerCluster/status/(.*)", CheckContainerStatusHandler),
    #(r"/containerCluster/remove", RemoveContainerClusterHandler),
    (r"/inner/MclusterManager/status/(.*)", StartMclusterManagerHandler),
    (r"/inner/container", ContainerHandler),
    #(r"/container/remove", RemoveContainerHandler),
    (r"/container/start", StartContainerHandler),
    (r"/container/stop", StopContainerHandler),
    (r"/container/status/(.*)", CheckContainerStatusHandler),
]