'''
Created on 2015-2-5

@author: asus
'''

class MysqlContainerClusterConfig(object):
    '''
    classdocs
    '''


    def __init__(self, params={}):
        '''
        Constructor
        '''
        self.__init_params(params)
    
    def __init_params(self, params):
            
        self.is_res_verify = True
        self.nodeCount = 3
        self.need_validate_manager_status = True
        self.mem_free_limit = 1*1024*1024*1024                      #default value stand for 10G                  
        mem_limit = params.get('mem_limit')                          #default value stand for 512M
        self.mem_limit = mem_limit if mem_limit else 512*1024*1024
        
        image = params.get('image')
        self.image = image if image else 'letv/mcluster:0.0.2'
        
        self.mount_dir = {'/srv/mcluster':'', '/data/mcluster_data':'/data/mcluster_data'}
        self.ports = [2181,2888,3306,3888,4567,4568,4569]
        