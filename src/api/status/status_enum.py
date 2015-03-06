#!/usr/bin/env python
#-*- coding: utf-8 -*-


class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

_status = ['starting', 'started', 'stopping', 'stopped', 'destroying', 'destroyed', 
           'not_exist', 'alive', 'failed', 'crisis', 'danger', 'succeed']

Status = Enum(_status)
