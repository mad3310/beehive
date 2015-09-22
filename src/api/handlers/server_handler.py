'''
Created on Sep 8, 2014

@author: root
'''
import logging

from tornado.web import asynchronous
from base import APIHandler
from server.serverOpers import Server_Opers
from resource_letv.serverResourceOpers import Server_Res_Opers
from utils.exceptions import HTTPAPIError
from tornado_letv.tornado_basic_auth import require_basic_auth
from container.containerOpers import Container_Opers


class UpdateServerHandler(APIHandler):
    """
    update server container 
    """
    
    server_opers = Server_Opers()
    
    def get(self):
        self.server_opers.update()
        return_message = {}
        return_message.setdefault("message", "update server successful")
        self.finish(return_message)


class CollectServerResHandler(APIHandler):
    _server_res_opers = Server_Res_Opers()
    
    _server_opers = Server_Opers()
    
    # eg. curl http://localhost:8888/server/resource
    @asynchronous
    def get(self):
        server_res = self._server_res_opers.retrieve_host_stat()
        self.finish(server_res)


class BaseServerHandler(APIHandler):

    container_opers=Container_Opers()

    @staticmethod
    def parse_container_name_list(container_name_list):
        if container_name_list:
            return container_name_list.split(',')
        else:
            raise HTTPAPIError(status_code=417, error_detail="containerNameList params not given!",\
                                notification = "direct", \
                                log_message= "containerNameList params not given!",\
                                response =  "please check params!")


@require_basic_auth
class SwitchServerUnderoomHandler(BaseServerHandler):

    container_opers = Container_Opers()

    # eg. curl --user root:root -d "switch=on&containerNameList=d-mcl-dh-n-1" "http://10.154.156.150:8888/server/containers/under_oom"
    def post(self):
        args = self.get_all_arguments()
        switch = args.get('switch')
        
        if not switch or (switch!='on' and switch!='off'):
            raise HTTPAPIError(status_code=417, error_detail="switch params wrong!",\
                                notification = "direct", \
                                log_message= "switch params wrong!",\
                                response =  "please check params!")
        
        containers = args.get('containerNameList')
        containerNameList = self.parse_container_name_list(containers)

        result = {}
        if switch == 'on':
            result = self.container_opers.open_containers_under_oom(containerNameList)
        elif switch == 'off':
            result = self.container_opers.shut_containers_under_oom(containerNameList)
        
        logging.debug('under_oom result: %s' % str(result))
        self.finish(result)


@require_basic_auth
class SetServerContainersDiskBpsHandler(BaseServerHandler):

    def post(self):
        args=self.get_all_arguments()
        containers=args.get('containerNameList')
        type=args.get('containerType')
        method=args.get('method')
        data=int(args.get('data',0))
        container_name_list=self.parse_container_name_list(containers)
        result=self.container_opers.set_containers_disk_bps(container_name_list,type,method,data)
        logging.debug('set disk bps result: %s' % result)
        self.finish(result)


@require_basic_auth
class SetServerContainersDiskIopsHandler(BaseServerHandler):

    def post(self):
        args=self.get_all_arguments()
        containers=args.get('containerNameList')
        type=args.get('containerType')
        method=args.get('method')
        times=int(args.get('times',0))
        container_name_list=self.parse_container_name_list(containers)
        result=self.container_opers.set_containers_disk_iops(container_name_list,type,method,times)
        logging.debug('set disk iops result: %s' % result)
        self.finish(result)


@require_basic_auth
class GatherServerContainersDiskLoadHandler(BaseServerHandler):
    """get the disk container use server 
    
    """
    
    container_opers = Container_Opers()
    
    # eg. curl --user root:root -d "containerNameList=d-mcl-4_zabbix2-n-2" http://localhost:8888/server/containers/disk
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        container_name_list = self.parse_container_name_list(containers)
        
        host_ip = self.request.remote_ip
        
        result = self.container_opers.get_containers_disk_load(container_name_list)
        logging.debug('get disk load on this server:%s, result:%s' %( host_ip, str(result)) )
        self.finish(result)


@require_basic_auth
class AddServerMemoryHandler(BaseServerHandler):
    
    container_opers = Container_Opers()
    
    # eg. curl --user root:root -d "containerNameList=d-mcl-4_zabbix2-n-2&times=2" http://10.154.156.150:8888/server/containers/memory/add
    @asynchronous
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        times = args.get('times')
        container_name_list = self.parse_container_name_list(containers)
        
        host_ip = self.request.remote_ip
        
        result = self.container_opers.add_containers_memory(container_name_list, int(times) )
        logging.info('add containers :%s memory on this server:%s, result:%s' % ( str(container_name_list), host_ip, str(result)) )
        self.finish(result)
