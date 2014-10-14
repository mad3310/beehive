'''
Created on Sep 8, 2014

@author: root
'''

class Server_Opers(object):
    '''
    classdocs
    '''
    def retrieveServerResource(self):
        resource = {'memoryCount':3,'diskCount':500}
        return resource
    
    def memory_stat(self):  
        mem = {}  
        f = open("/proc/meminfo")  
        lines = f.readlines()  
        f.close()  
        for line in lines:  
            if len(line) < 2: continue  
            name = line.split(':')[0]  
            var = line.split(':')[1].split()[0]  
            mem[name] = long(var) * 1024.0  
        mem['MemUsed'] = mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached']  
        return mem['MemFree']
    
    def cpu_stat(self):  
        cpu = []  
        cpuinfo = {}  
        f = open("/proc/cpuinfo")
        lines = f.readlines() 
        f.close()  
        for line in lines:  
            if line == '\n':  
                cpu.append(cpuinfo)  
                cpuinfo = {}  
            if len(line) < 2: continue  
            name = line.split(':')[0].rstrip()  
            var = line.split(':')[1]  
            cpuinfo[name] = var  
        return cpu
    
    def load_stat(self):  
        loadavg = {}  
        f = open("/proc/loadavg")  
        con = f.read().split()  
        f.close()  
        loadavg['lavg_1']=con[0]  
        loadavg['lavg_5']=con[1]  
        loadavg['lavg_15']=con[2]  
        loadavg['nr']=con[3]  
        loadavg['last_pid']=con[4]  
        return loadavg 

if __name__ == '__main__':
    server = Server_Opers()
    print server.load_stat()
        