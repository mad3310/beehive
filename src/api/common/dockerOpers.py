'''
Created on Sep 8, 2014

@author: root
'''

import logging, traceback
from docker import Client as client

class Docker_Opers(client):
    '''
    classdocs
    '''
    def __init__(self):
        super(Docker_Opers, self).__init__(base_url='unix://var/run/docker.sock')
    
    def start(self, container, binds=None, port_bindings=None, lxc_conf=None,
              publish_all_ports=False, links=None, privileged=False,
              dns=None, dns_search=None, volumes_from=None, network_mode=None):
        try:
            c = client()
            c.start(container, binds, port_bindings, lxc_conf, publish_all_ports, links,
                    privileged, dns, dns_search, volumes_from, network_mode)
        except:
            logging.error( str(traceback.format_exc()) )
       
    def stop(self, container, timeout=20):
        try:
            c = client()
            c.stop(container, timeout)
        except:
            logging.error( str(traceback.format_exc()) )
    
    def kill(self, container, signal=None):
        try:
            c = client()
            c.kill(container, signal)
        except:
            logging.error( str(traceback.format_exc()) )    
    
    def remove_container(self, container, v=False, link=False, force=False):
        try:
            c = client()
            c.remove_container(container, v, link, force)
        except:
            logging.error( str(traceback.format_exc()) )      
    
    def destroy(self, container):
        self.kill(container)
        self.remove_container(container, force=True)
    
    def containers(self, quiet=False, all=False, trunc=True, latest=False,
                   since=None, before=None, limit=-1, size=False):
        c = client()
        return c.containers(quiet, all, trunc, latest, since, before, limit, size)
        
    def inspect_container(self, container):
        c = client()
        return c.inspect_container(container)
    
if __name__ == '__main__':
    d = Docker_Opers()
    print d.inspect_container('d-mcl-djimlwy-n-1')
