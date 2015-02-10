'''
Created on 2015-2-5

@author: asus
'''

class GbalancerContainerClusterConfig(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.is_res_verify = True
        self.nodeCount = 1
        self.need_validate_manager_status = False
        self.mem_free_limit = 10*1024*1024*1024           #stand for 10G                  
        self.mem_limit = 512*1024*1024                    #stand for 512M