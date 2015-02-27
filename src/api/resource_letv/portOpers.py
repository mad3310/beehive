'''
Created on 2015-2-8

@author: asus
'''
import logging

class PortOpers(object):
    '''
    classdocs
    '''
    '''
    @todo: why use Queue? List?
    '''
#     store_illegal_ips_queue = Queue.Queue()
#     store_all_ips_queue = Queue.Queue()
# 
#     zkOper = ZkOpers('127.0.0.1', 2181)
#     
#     docker_opers = Docker_Opers()
#     
#     def __init__(self):
#         '''
#         constructor
#         '''
#     
#     def write_into_portPool(self, args_dict):
#         ip_segment = args_dict.get('ipSegment')
#         ip_count = int(args_dict.get('ipCount'))
#         choosed_ip = self._get_needed_ips(ip_segment, ip_count)
#         for host_ip in choosed_ip:
#             self.zkOper.write_port_into_portPool(host_ip, port)
#     
#     def _get_needed_ips(self, ip_segment, ip_count):
#         choosed_ip = []
#         ip_list = self.zkOper.get_ips_from_ipPool()
#         ips = list( set(all_ips) - set(ip_list) )
#         num = 0
#         if len(ips) < ip_count:
#             raise CommonException('the ips of this segment is less the the number you need, please apply less ips')
#         for ip in ips:
#             if self.__ip_legal(ip):
#                 choosed_ip.append(ip)
#                 num += 1
#             if num == ip_count:
#                 break
#         return choosed_ip
# 
#     def __ip_legal(self, ip):
#         '''
#         @todo: same as utils.autoutil.ping_ip_able?
#         '''
#         cmd = 'ping -w 2 %s' % str(ip)
#         ret = os.system(cmd)
#         if not ret:
#             logging.info('ping ip: %s result :%s' % (ip, str(ret)) )
#             return False
#         
#         host_con_ip_list = self.docker_opers.retrieve_containers_ips()
#         if ip in host_con_ip_list:
#             return False
#         return True
# 
#         
#     def __ips_legal(self):
#         """
#         """
#         while not self.store_all_ips_queue.empty():
#             ip = self.store_all_ips_queue.get(block=False)
#             is_lagel = self.__ip_legal(ip)
#             if not is_lagel:
#                 self.store_illegal_ips_queue.put(ip)
# 
#     def get_illegal_ips(self, thread_num):
#         """check ip pools
#            
#            thread_num: how many thread to do check if ip is legal
#            put all ips in ip pools into store_all_ips_queue,
#            do check ip is legal in  threads, if illegal, put illegal ip into store_illegal_ips_queue,
#            if all threads end, get illegal ips and return them
#         """
#         
#         illegal_ips, thread_obj_list = [], []
#         ip_list = self.zkOper.get_ips_from_ipPool()
#         logging.info('ips in ip pool:%s' % str(ip_list) )
#         
#         logging.info('put all ips in ip pools into store_all_ips_queue')
#         
#         self.store_all_ips_queue._init(0)
#         self.store_all_ips_queue.queue.extend(ip_list)
#         
#         logging.info('queue size :%s' % str(self.store_all_ips_queue.qsize()) )
#         for i in range(thread_num):
#             thread_obj = doInThread(self.__ips_legal)
#             thread_obj_list.append(thread_obj)
#         
#         while thread_obj_list:
#             succ = []
#             for thread_obj in thread_obj_list:
#                 if not thread_obj.isAlive():
#                     succ.append(thread_obj)
#             for item in succ:
#                 thread_obj_list.remove(item)
#             time.sleep(0.5)
#         
#         logging.info('get illegal_ip')
#         while not self.store_illegal_ips_queue.empty():
#             illegal_ip = self.store_illegal_ips_queue.get(block=False)
#             illegal_ips.append(illegal_ip)
#         logging.info('illegal_ips :%s' % str(illegal_ips) )
#         return illegal_ips
    
    def retrieve_port_resource(self, host_ip_list, every_host_port_count=1):
        port_dict = {}
        isLock,lock = self.zkOper.lock_assign_port()
        try:
            if isLock:
                for host_ip in host_ip_list:
                    port_dict.setdefault(self.zkOper.retrieve_port(host_ip, every_host_port_count))
        finally:
            if isLock:
                self.zkOper.unLock_assign_port(lock)
        return port_dict
        