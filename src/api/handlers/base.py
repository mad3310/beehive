#!/usr/bin/env python
#-*- coding: utf-8 -*-

from tornado.web import RequestHandler,HTTPError
from tornado import escape
from tornado.options import options

from utils.exceptions import HTTPAPIError, UserVisiableException
from utils.mail import send_email
from utils.invokeCommand import InvokeCommand
from utils import getHostIp

import logging
import traceback

class BaseHandler(RequestHandler):
    
    logger = logging.getLogger('root')

    def get_all_arguments(self):
        request_param = {}
        args = self.request.arguments
        for key in args:
            request_param.setdefault(key, args[key][0])
        return request_param
    
class APIHandler(BaseHandler):
    def finish(self, chunk=None, notification=None):
        if chunk is None:
            chunk = {}

        if isinstance(chunk, dict):
            if 'error_code' not in chunk.keys():
                chunk = {"meta": {"code": 200}, "response": chunk}
            else:
                chunk = {"meta": {"code ": 401}, "response": chunk}
            if notification:
                chunk["notification"] = {"message": notification}

        callback = escape.utf8(self.get_argument("callback", None))
        if callback:
            self.set_header("Content-Type", "application/x-javascript")

            if isinstance(chunk, dict):
                chunk = escape.json_encode(chunk)

            self._write_buffer = [callback, "(", chunk, ")"] if chunk else []
            super(APIHandler, self).finish()
        else:
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            super(APIHandler, self).finish(chunk)

    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages."""
        debug = self.settings.get("debug", False)
        try:
            exc_info = kwargs.pop('exc_info')
            e = exc_info[1]

            if isinstance(e, HTTPAPIError):
                pass
            elif isinstance(e, UserVisiableException):
                user_message = e.__str__()
                e = HTTPAPIError(417, error_detail=user_message)
                status_code = e.status_code
            elif isinstance(e, HTTPError):
                e = HTTPAPIError(e.status_code)
            else:
                e = HTTPAPIError(500)

            exception = "".join([ln for ln in traceback.format_exception(*exc_info)])

            if status_code == 500 and not debug:
                logging.error(e)
                self._send_error_email(exception)

            if debug:
                e.response["exception"] = exception

            self.clear()
            self.set_status(200)  # always return 200 OK for API errors
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(str(e))
        except Exception:
            logging.error(traceback.format_exc())
            return super(APIHandler, self).write_error(status_code, **kwargs)

    def _send_error_email(self, exception):

        try:
            local_ip = getHostIp()
            invokeCommand = InvokeCommand()
            cmd_str = "rpm -qa nginx-manager"
            version_str = invokeCommand._runSysCmd(cmd_str)
            logging.info("version_str :" + str(version_str)) 
            # send email
            subject = "[%s]Internal Server Error " % options.sitename
            body = self.render_string("../templates/errors/500_email.html",
                                      exception=exception)
            
            body += "\n" + version_str[0] + "\nip:" + local_ip
            
#            email_from = "%s <noreply@%s>" % (options.sitename, options.domain)
            if options.send_email_switch:
                send_email(options.admins, subject, body)
        except Exception:
            logging.error(traceback.format_exc())


class ErrorHandler(RequestHandler):
    """Default 404: Not Found handler."""
    def prepare(self):
        super(ErrorHandler, self).prepare()
        raise HTTPError(404)


class APIErrorHandler(APIHandler):
    """Default API 404: Not Found handler."""
    def prepare(self):
        super(APIErrorHandler, self).prepare()
        raise HTTPAPIError(404)
