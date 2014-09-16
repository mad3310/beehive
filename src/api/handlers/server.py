'''
Created on Sep 8, 2014

@author: root
'''
from handlers.base import APIHandler
from common.serverOpers import Server_Opers

class ServerHandler(APIHandler):
    '''
    classdocs
    '''
    serverOpers = Server_Opers()

    def get(self):
        dict = self.serverOpers.retrieveServerResource()
        return self.finish(dict)