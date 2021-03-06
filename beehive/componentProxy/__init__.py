
_path = {
    "nginx": "componentProxy.webcontainer",
    "mcluster": "componentProxy.db",
    "gbalancer": "componentProxy.loadbalance",
    "jetty": "componentProxy.webcontainer",
    "tomcat": "componentProxy.webcontainer",
    "gbalancerCluster": "componentProxy.loadbalance",
    "cbase": "componentProxy.store",
    "zookeeper": "componentProxy.distribution",
    "elasticsearch": "componentProxy.elk",
    "logstash": "componentProxy.elk",
    "kibana": "componentProxy.elk",
}

_name = {
    "nginx": "ngx",
    "mcluster": "mcl",
    "gbalancer": "gbl",
    "jetty": "jty",
    "tomcat": "tmt",
    "gbalancerCluster": "gbc",
    "cbase": "cbs",
    "logstash": "lgs",
    "zookeeper": "zkp",
    "kibana": "kbn",
    "elasticsearch": "esh",
}

_mount_dir = {
    "nginx": "/var/log",
    "mcluster": "/srv/docker/vfs",
    "gbalancer": "/var/log",
    "jetty": "/var/log",
    "tomcat": "/var/log",
    "gbalancerCluster": "/var/log",
    "cbase": "/opt/letv",
    "logstash": "/var/log",
    "zookeeper": "/var/log",
    "kibana": "/var/log",
    "elasticsearch": "/srv/docker/vfs",
}
