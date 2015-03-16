'''
Created on 2015-2-1

@author: asus
'''

class Docker_Model(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._image = image
    
    @property    
    def hostname(self):
        return self._hostname
    
    @hostname.setter
    def hostname(self, hostname):
        self._hostname = hostname
        
    @property
    def user(self):
        return self._user
    
    @user.setter
    def user(self, user):
        self._user = user
        
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name = name
    
    @property    
    def environment(self):
        return self._environment
    
    @environment.setter
    def environment(self, environment):
        self._environment = environment
    
    @property   
    def tty(self):
        return self._tty
    
    @tty.setter
    def tty(self, tty):
        self._tty = tty
        
    @property
    def ports(self):
        return self._ports
    
    @ports.setter
    def ports(self, ports):
        self._ports = ports
    
    @property    
    def stdin_open(self):
        return self._stdin_open
    
    @stdin_open.setter
    def stdin_open(self, stdin_open):
        self._stdin_open = stdin_open
    
    @property    
    def mem_limit(self):
        return self._mem_limit
    
    @mem_limit.setter
    def mem_limit(self, mem_limit=1):
        self._mem_limit = mem_limit
    
    @property        
    def volumes(self):
        return self._volumes
    
    @volumes.setter
    def volumes(self, volumes):
        self._volumes = volumes
    
    @property    
    def binds(self):
        return self._binds
    
    @binds.setter
    def binds(self, binds):
        self._binds = binds
    
    @property        
    def privileged(self):
        return self._privileged
    
    @privileged.setter
    def privileged(self, privileged=False):
        self._privileged = privileged
    
    @property    
    def network_mode(self):
        return self._network_mode
    
    @network_mode.setter
    def network_mode(self, network_mode='bridge'):
        self._network_mode = network_mode
    
    @property    
    def use_ip(self):
        return self._use_ip
    
    @use_ip.setter
    def use_ip(self, use_ip=False):
        self._use_ip = use_ip

    @property
    def component_type(self):
        return self._component_type
    
    @component_type.setter
    def component_type(self, component_type):
        self._component_type = component_type

    @property
    def port_bindings(self):
        return self._port_bindings
    
    @port_bindings.setter
    def port_bindings(self, port_bindings):
        self._port_bindings = port_bindings
        