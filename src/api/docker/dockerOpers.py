'''
Created on Sep 8, 2014

@author: root
'''

from docker import Client as client

class Docker_Opers(client):
    '''
    classdocs
    '''
    client = client()
    
    def __init__(self):
        super(Docker_Opers, self).__init__(base_url='unix://var/run/docker.sock')
        
    def create(self,image,hostname,user='root',name,environment,tty=True,ports,stdin_open=True,mem_limit,volumes):
        container_id = self.client.create_container(image, 
                                                    hostname, 
                                                    user,
                                                    name, 
                                                    environment, 
                                                    tty, 
                                                    ports, 
                                                    stdin_open,
                                                    mem_limit, 
                                                    volumes)
        return container_id
    
    def start(self, container, binds=None, port_bindings=None, lxc_conf=None,
              publish_all_ports=False, links=None, privileged=False,
              dns=None, dns_search=None, volumes_from=None, network_mode=None):
        self.client.__start(container, 
                          binds, 
                          port_bindings, 
                          lxc_conf, 
                          publish_all_ports, 
                          links,
                          privileged, 
                          dns, 
                          dns_search, 
                          volumes_from, 
                          network_mode)
       
    def stop(self, container, timeout=20):
        self.client.stop(container, timeout)
    
    def kill(self, container, signal=None):
        self.client.kill(container, signal)
    
    def remove_container(self, container, v=False, link=False, force=False):
        self.client.remove_container(container, v, link, force)
    
    def destroy(self, container):
        self.kill(container)
        self.remove_container(container, force=True)
    
    def containers(self, quiet=False, all=False, trunc=True, latest=False,
                   since=None, before=None, limit=-1, size=False):
        return self.client.containers(quiet, 
                                      all, 
                                      trunc, 
                                      latest, 
                                      since, 
                                      before, 
                                      limit, 
                                      size)
        
    def inspect_container(self, container):
        return self.client.inspect_container(container)
    
if __name__ == '__main__':
    d = Docker_Opers()
    print d.inspect_container('d-mcl-djimlwy-n-1')
