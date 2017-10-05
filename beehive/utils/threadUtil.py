'''
Created on Apr 4, 2015

@author: root
'''
import threading

def doInThread(func, *params, **kwargs):
    ft = FuncThread(func, *params, **kwargs)
    ft.start()
    return ft

class FuncThread(threading.Thread):
    def __init__(self, func, *params, **paramMap):
        threading.Thread.__init__(self)
        self.func = func
        self.params = params
        self.paramMap = paramMap
        self.rst = None
        self.finished = False

    def run(self):
        self.rst = self.func(*self.params, **self.paramMap)
        self.finished = True

    def getResult(self):
        return self.rst

    def isFinished(self):
        return self.finished