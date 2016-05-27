'''
Created on Sep 8, 2014

@author: root
'''
import logging

from tornado.web import asynchronous
from tornado.gen import engine
from base import APIHandler
from utils.exceptions import HTTPAPIError, UserVisiableException
from tornado_letv.tornado_basic_auth import require_basic_auth
from container.containerOpers import Container_Opers
from server.serverOpers import Server_Opers
from image.imageOpers import ImageOpers
from utils.decorators import run_callback, run_on_executor



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
    """refer to wiki: http://wiki.letv.cn/pages/viewpage.action?pageId=48637217
    
    containerType :  component type
    method :  write or read
    date : Byte per second limit
    eg. curl --user root:root -d "containerNameList=d-mcl-zz-n-3&containerType=mcluster&method=write&data=500" http://localhost:8888/server/containers/disk/bps
    """

    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        _type = args.get('containerType')
        method = args.get('method')
        data = int(args.get('data', 0))
        container_name_list = self.parse_container_name_list(containers)
        result = self.container_opers.set_containers_disk_bps(container_name_list, _type, method, data)
        logging.debug('set disk bps result: %s' % result)
        self.finish(result)


@require_basic_auth
class SetServerContainersDiskIopsHandler(BaseServerHandler):
    """refer to wiki: http://wiki.letv.cn/pages/viewpage.action?pageId=48637217
    
    containerType :  component type
    method :  write or read
    date : times per second limit
    
    eg. curl --user root:root -d "containerNameList=d-mcl-zz-n-3&containerType=mcluster&method=write&times=50" http://localhost:8888/server/containers/disk/iops
    """
    
    def post(self):
        args = self.get_all_arguments()
        containers = args.get('containerNameList')
        _type = args.get('containerType')
        method = args.get('method')
        times = int(args.get('times', 0))
        container_name_list = self.parse_container_name_list(containers)
        result = self.container_opers.set_containers_disk_iops(container_name_list, _type, method, times)
        logging.debug('set disk iops result: %s' % result)
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


class SyncServerHandler(APIHandler):
    """
    update server container 
    """
    
    server_opers = Server_Opers()
    
    def get(self):
        self.server_opers.sync()
        return_message = {}
        return_message.setdefault("message", "update server successful")
        self.finish(return_message)


class PullImageToServerHandler(APIHandler):
    
    image_opers = ImageOpers()
    
    @asynchronous
    @engine
    def post(self):
        """
            eg. curl --user root:root -d "image=xxx" http://127.0.0.1:8888/server/image/pull
        """
        
        args = self.get_all_arguments()
        image = args.get('image')
        logging.info('create container image :%s' % image)
        
        #if not self.image_opers.check_image_name_legal(image):
        #    raise UserVisiableException('image name %s is not legal, please check the image name~' % image)

        ret = yield self.do(image)
        self.finish({'result':ret})

    @run_on_executor()
    @run_callback
    def do(self, image):
        return self.image_opers.pull(image)
