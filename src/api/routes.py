#!/usr/bin/env python
#-*- coding: utf-8 -*-

from handlers.serverCluster import ServerClusterHandler
from handlers.server import ServerHandler
from handlers.containerCluster import ContainerClusterHandler
from handlers.container import ContainerHandler
from handlers.admin import AdminConf, AdminUser, AdminReset

handlers = [
    (r"/admin/conf", AdminConf),
    (r"/admin/user", AdminUser),
    (r"/admin/reset", AdminReset),
    (r"/serverCluster", ServerClusterHandler),
    (r"/server", ServerHandler),
    (r"/containerCluster", ContainerClusterHandler),
    (r"/inner/container", ContainerHandler)
]