import threading
import logging

from zkOpers import ZkOpers
from utils.threading_exception_queue import Threading_Exception_Queue
from utils.mail import send_email
from configFileOpers import ConfigFileOpers
from tornado.options import options

class Abstract_Async_Thread(threading.Thread):
    
    zkOper = ZkOpers('127.0.0.1',2181)
    
    threading_exception_queue = Threading_Exception_Queue()
    
    confOpers = ConfigFileOpers()
    
    def __init__(self):
        threading.Thread.__init__(self)
        
    def _send_email(self, data_node_ip, text):
        try:
            # send email
            subject = "[%s] %s" % (data_node_ip, text)
            body = "[%s] %s" % (data_node_ip, text)
            
#            email_from = "%s <noreply@%s>" % (options.sitename, options.domain)
            if options.send_email_switch:
                send_email(options.admins, subject, body)
        except Exception,e:
            logging.error("send email process occurs error", e)