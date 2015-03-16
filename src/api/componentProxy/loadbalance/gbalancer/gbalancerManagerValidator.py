#-*- coding: utf-8 -*-


class GbalanceManagerValidator(object):
    
    def __init__(self):
        self.timeout = 5
        
    
    def validate_manager_status(self, num):
        """webportal use gbalancer-manager to start gbalancer 
        
        """
        
        return True