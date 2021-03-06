# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 feilong.me. All rights reserved.
#
# @author: Felinx Lee <felinx.lee@gmail.com>
# Created on  Jun 30, 2012
#

from tornado import escape
from tornado.web import HTTPError


class HTTPAPIError(HTTPError):
    """API error handling exception

    API server always returns formatted JSON to client even there is
    an internal server error.
    """
    def __init__(self, status_code=400, error_detail="", error_type="",
                 notification="", response="", log_message=None, *args):

        super(HTTPAPIError, self).__init__(int(status_code), log_message, *args)

        self.error_type = error_type if error_type else \
            _error_types.get(self.status_code, "unknow_error")
        self.error_detail = error_detail
        self.notification = {"message": notification} if notification else {}
        self.response = response if response else {}

    def __str__(self):
        err = {"meta": {"code": self.status_code, "errorType": self.error_type}}
        self._set_err(err, ["notification", "response"])

        if self.error_detail:
            err["meta"]["errorDetail"] = self.error_detail

        return escape.json_encode(err)

    def _set_err(self, err, names):
        for name in names:
            v = getattr(self, name)
            if v:
                err[name] = v

class CommonException(Exception):
    def __init__(self, value):
        super(CommonException, self).__init__(
            "Common Exception. Error Message %s " % (value))
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class RetryException(Exception):
    def __init__(self, value):
        super(RetryException, self).__init__(
            "Retry Exception. Error Message %s " % (value))
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class ImageNotFoundError(Exception):
    def __init__(self, image, tag):
        super(ImageNotFoundError, self).__init__(
            "Image %s with tag %s not found." % (image, tag))
        
class UserVisiableException(CommonException):
    def __init__(self, value):
        super(UserVisiableException, self).__init__(value)
        
class ZKLockException(CommonException):
    def __init__(self, value):
        super(ZKLockException, self).__init__(value)

_error_types = {400: "param_error",
                401: "invalid_auth",
                403: "not_authorized",
                404: "endpoint_error",
                405: "method_not_allowed",
                417: "user_visible_error",
                500: "server_error",
                578: "conncurrency_error",
                579: "resource_error"
                }
