
_path = {
    "nginx":"componentProxy.webcontainer",
    "mcluster":"componentProxy.db",
    "gbalancer":"componentProxy.loadbalance",
    "jetty":"componentProxy.webcontainer",
    "gbalancerCluster":"componentProxy.loadbalance",
    "cbase":"componentProxy.store",
    "logstash":"componentProxy.webcontainer",
    "zookeeper":"componentProxy.distribution",
}

_name = {
    "nginx":"ngx",
    "mcluster":"mcl",
    "gbalancer":"gbl",
    "jetty":"jty",
    "gbalancerCluster":"gbc",
    "cbase":"cbs",
    "logstash":"lgs",
    "zookeeper":"zkp",
}

_mount_dir = {
    "nginx":"/var/log",
    "mcluster":"/srv/docker/vfs",
    "gbalancer":"/var/log",
    "jetty":"/var/log",
    "gbalancerCluster":"/var/log",
    "cbase":"/opt/letv",
    "logstash":"/var/log",
    "zookeeper":"/var/log",
}