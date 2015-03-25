'''
Created on 2015-2-4

@author: asus
'''

from componentProxy.db.mysql.mclusterOper import MclusterManager
from componentProxy.loadbalance.gbalancer.gbalancerOper import GbalancerManager
from componentProxy.webcontainer.nginx.nginxOper import NginxManager
from componentProxy.webcontainer.jetty.jettyOper import JettyManager

class ComponentManagerStatusValidator(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

    '''
    @todo: study the importlib way to replace if else, even if condition is limit, use dict way to replace it
    '''        
    def start_status_validator(self, component_type, container_name):
        _check_result = False
        if "mclusternode" == component_type:
            manager_validator = MclusterManager()
        elif "mclustervip" == component_type:
            manager_validator = GbalancerManager()
        elif "nginx" == component_type:
            manager_validator = NginxManager()
        elif "jetty" == component_type:
            manager_validator = JettyManager()
        else:
            manager_validator = None
        
        _check_result = manager_validator.manager_status(container_name)
        return _check_result
