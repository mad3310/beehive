'''
Created on 2015-2-1

@author: asus
'''
from componentProxy.db.mysql.mysqlContainerModelCreator import MySQLContainerModelCreator
from componentProxy.webcontainer.nginx.nginxContainerModelCreator import NginxContainerModelCreator
from componentProxy.loadbalance.gbalancer.gbalancerContainerModelCreator import GbalancerContainerModelCreator
from componentProxy.webcontainer.jetty.jettyContainerModelCreator import JettyContainerModelCreator
from componentProxy.store.cbase.cbaseContainerModelCreator import CbaseContainerModelCreator


class ComponentContainerModelFactory(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    def create(self, args={}):
        _component_type = args.get('componentType')
        
        if "mclustervip" == _component_type:
            creator = GbalancerContainerModelCreator()
        elif "mclusternode" == _component_type:
            creator = MySQLContainerModelCreator()
        elif "nginx" == _component_type:
            creator = NginxContainerModelCreator()
        elif "jetty" == _component_type:
            creator = JettyContainerModelCreator()
        elif "cbase" == _component_type:
            creator = CbaseContainerModelCreator()
        else:
            pass
        
        _arg_list = creator.create(args)
        return _arg_list