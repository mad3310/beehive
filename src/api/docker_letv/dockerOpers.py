'''
Created on Sep 8, 2014

@author: root
'''

from utils import _get_property_dict
from docker import Client as client


class Docker_Opers(client):
    '''
    classdocs
    '''
    client = client()
    
    def __init__(self):
        super(Docker_Opers, self).__init__(base_url='unix://var/run/docker.sock')
        

    def create(self, docker_model):
        
        entry = _get_property_dict(docker_model)
        image = entry['image']
        
        tty = entry['tty'] if 'tty' in entry else True
        stdin_open = entry['stdin_open'] if 'stdin_open' in entry else True
        
        kwargs = {
            'image': image,
            'user': 'root',
            'detach': False,
            'tty' : tty,
            'stdin_open':stdin_open,
        }

        if 'name' in entry:
            kwargs['name'] = entry['name']

        if 'volumes' in entry:
            kwargs['volumes'] = entry['volumes']

        if 'environment' in entry:
            kwargs['environment'] = entry['environment']

        if 'hostname' in entry:
            kwargs['hostname'] = entry['hostname']

        if 'cpu_shares' in entry:
            kwargs['cpu_shares'] = entry['cpu_shares']

        if 'mem_limit' in entry:
            kwargs['mem_limit'] = entry['mem_limit']

        if 'entrypoint' in entry:
            kwargs['entrypoint'] = entry['entrypoint']

        if 'command' in entry:
            kwargs['command'] = entry['command']

        if 'ports' in entry:
            kwargs['ports'] = entry['ports']
            
        container = self.client.create_container(**kwargs)
        
        #self.docker_start(docker_model)
        
        return container['Id']
           
    def start(self, docker_model):
        
        container = docker_model.name
        entry = _get_property_dict(docker_model)
        privileged = entry['privileged'] if 'privileged' in entry else True
        network_mode = entry['network_mode'] if 'network_mode' in entry else 'bridge'
        
        kwargs = {
            'container': container,
            'network_mode':network_mode, 
            'privileged' : privileged
        }

        if 'binds' in entry:
            kwargs['binds'] = entry['binds']

        if 'network' in entry:
            kwargs['network_mode'] = entry['network']

        if 'privileged' in entry:
            kwargs['privileged'] = entry['privileged']

        if 'lxc_conf' in entry:
            kwargs['lxc_conf'] = entry['lxc_conf']

        if 'volumes_from' in entry:
            kwargs['volumes_from'] = entry['volumes_from']

        if 'port_bindings' in entry:
            kwargs['port_bindings'] = entry['port_bindings']

        if 'links' in entry:
            kwargs['links'] = entry['links']

        if 'dns' in entry:
            kwargs['dns'] = entry['dns']

        if 'dns_search' in entry:
            kwargs['dns_search'] = entry['dns_search']

        if 'publish_all_ports' in entry:
            kwargs['publish_all_ports'] = entry['publish_all_ports']

        self.client.start(**kwargs);
       
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
    
    def image_name_list(self):
        image_list = []
        images = self.client.images()
        for image in images:
            for k,v in image.items():
                if k == 'RepoTags':
                    image_list.append(v)
        return image_list

    def image_id_list(self):
        self.client.images(quiet=True)

if __name__ == '__main__':
    d = Docker_Opers()
    print d.inspect_container('d-mcl-djimlwy-n-1')
