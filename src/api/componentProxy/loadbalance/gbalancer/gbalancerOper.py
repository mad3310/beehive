#-*- coding: utf-8 -*-


class GbalanceManager(object):
    
    def __init__(self):
        self.timeout = 5
        
    '''
    @todo: no need to check, only return True?
    '''
    def manager_status(self, container_name = None):
        return True