'''
Created on 2015-2-5

@author: asus
'''

class MysqlContainerClusterConfig(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.is_res_verify = True
        self.nodeCount = 3
        self.need_validate_manager_status = True
        self.mem_free_limit = 10
        self.mem_limit = 512*1024*1024
        
        