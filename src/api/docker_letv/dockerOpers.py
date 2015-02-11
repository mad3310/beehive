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
        

    def create(self, docker_model):
        image = docker_model.image
        hostname = docker_model.hostname
        user = 'root'
        name = docker_model.name
        environment = docker_model.environment
        tty = True
        ports = docker_model.ports
        stdin_open = True
        mem_limit = docker_model.mem_limit
        volumes = docker_model.volumes
        
        container_id = self.client.create_container(image=image, 
                                                    hostname=hostname, 
                                                    user=user,
                                                    name=name, 
                                                    environment=environment, 
                                                    tty=tty, 
                                                    ports=ports, 
                                                    stdin_open=stdin_open,
                                                    mem_limit=mem_limit, 
                                                    volumes=volumes)
        return container_id
    
    def start(self, docker_model):
        container = docker_model.name
        binds = docker_model.binds
        port_bindings = None 
        lxc_conf = None
        publish_all_ports = False
        links = None
        privileged=True
        dns=None
        dns_search=None
        volumes_from=None
        network_mode='bridge'
        
        self.client.start(container=container, 
                            binds=binds, 
                            port_bindings=port_bindings, 
                            lxc_conf=lxc_conf, 
                            publish_all_ports=publish_all_ports, 
                            links=links,
                            privileged=privileged, 
                            dns=dns, 
                            dns_search=dns_search, 
                            volumes_from=volumes_from, 
                            network_mode=network_mode)
       
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
    
    '''
    @todo: need test
    '''
    def retrieve_containers_ids(self):
        containers_info = self.containers()
        id_list = []
        for container_iter in containers_info:
            id_list.append(container_iter['Id'])
        return id_list
    
    '''
    @todo: need test
    '''
    def retrieve_containers_ips(self):
        container_id_list = self.retrieve_containers_ids()
        ip_list = []
        for container_id_iter in container_id_list:
            env = self.inspect_container(container_id_iter)['Config']['Env']
            for item in env:
                if item.startswith("IP="):
                    ip_list.append(item.split("=")[1])
        return ip_list
    
if __name__ == '__main__':
    d = Docker_Opers()
    print d.inspect_container('d-mcl-djimlwy-n-1')
