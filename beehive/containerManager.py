#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import routes
import traceback
import logging
import logging.config

from tornado.options import options
from appdefine import appDefine
from scheduler.scheduler_tasks.schedulerOpers import SchedulerOpers
from check_sync import CheckSync
from es.serverRes import ServerRes

class Application(tornado.web.Application):
    def __init__(self):
        
        settings = dict(
                        templates_path=os.path.join(os.path.dirname(__file__), 'templates'),
                        debug=options.debug
                        )
        tornado.web.Application.__init__(self, routes.handlers, **settings)

def main():
    config_path = os.path.join(options.base_dir, "config")
    logging.config.fileConfig(config_path + '/logging.conf')
    ServerRes.connect(options.es_host)
    cs = CheckSync()
    cs.sync()

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    
    SchedulerOpers()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    try:
        main()
    except:
        logging.error( '%s' % str( traceback.print_exc()))
