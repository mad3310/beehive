import threading
import logging

from utils.threading_exception_queue import Threading_Exception_Queue
from utils.mail import send_email
from utils.configFileOpers import ConfigFileOpers
from utils import getHostIp
from utils.invokeCommand import InvokeCommand
from tornado.options import options


class Abstract_Async_Thread(threading.Thread):
    
    threading_exception_queue = Threading_Exception_Queue()
    
    confOpers = ConfigFileOpers()
    
    def __init__(self):
        threading.Thread.__init__(self)
        
    def _send_email(self, data_node_ip, text):
        try:
            # send email
            host_ip = getHostIp()
            invokeCommand = InvokeCommand()
            cmd_str = "rpm -qa container-manager"
            version_str = invokeCommand._runSysCmd(cmd_str)
            subject = "[%s] %s" % (data_node_ip, text)

            body = "[%s] %s" % (data_node_ip, text)
            body += "\n" + version_str[0] + "\nip:" + host_ip
            
#            email_from = "%s <noreply@%s>" % (options.sitename, options.domain)
            if options.send_email_switch:
                send_email(options.admins, subject, body)
        except Exception,e:
            logging.error("send email process occurs error", e)