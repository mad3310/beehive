#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on Sep 8, 2014

@author: Wangzhen
'''

import os, time
import logging
import docker

from utils.autoutil import *
from utils.invokeCommand import InvokeCommand
from docker_letv.dockerOpers import Docker_Opers


class Res_Opers():
    '''
    classdocs
    '''
    
    docker_c = docker.Client(base_url = 'unix://var/run/docker.sock')
    _logger = logging.getLogger("process_info")
    _logger.setLevel(logging.INFO)
    
    docker_opers = Docker_Opers()

    def __init__(self ,container_name = ""):
        self.name = container_name
        if self.name != "":
            self.matrix_list = self.get_top_cmd_ret()
            self.id_pid_dict = self.get_container_id_pid_dict(self.name)
    
    def retrieve_host_stat(self):
        resource = {}
        
        mem_res_info = self.memory_stat()
        resource.setdefault("mem_res", mem_res_info) 
        
        server_disk = self.disk_stat()
        resource.setdefault("server_disk", server_disk)

        # disk_over_load = self.disk_loadavg()
        # resource.setdefault("disk_over_load", disk_over_load)
        
#         disk_instant_spd = self.disk_instant_load()
#         resource.setdefault("disk_instant_spd", disk_instant_spd)
        
        # _cpu_info = self.cpu_info()
        # resource.setdefault("cpu_info" , _cpu_info)
       
#         cur_cpu_usage = self.get_cur_cpu_usage()
#         resource.setdefault("cur_cpu_idle", cur_cpu_usage)

#         cur_net_load = self.get_cur_net_load()
#         resource.setdefault("cur_net_load", cur_net_load)
        return resource
    
    def retrieve_container_stat(self):

        dict = {}
        dict.setdefault("container_alloc_mem",self.get_container_alloc_mem()) 
#         dict.setdefault("container_network_load",self.get_container_network_load())
#         dict.setdefault("container_disk_load", self.get_container_disk_load())
#         pid = self.id_pid_dict["pid_0"]
#         dict.setdefault("rss_cpu", self.search_pid_family_info(pid))
        return dict
    
    def get_containers_alloc_mem(self):
        
        total_mem = 0
        containers_id_list = self.docker_opers.retrieve_containers_ids()
        for container_id_iter in containers_id_list:
            print self.docker_c.inspect_container(container_id_iter)
            total_mem += self.docker_c.inspect_container(container_id_iter)['Config']['Memory']
        self._logger.info("The memory of all containers is :"+ str(total_mem/1024/1024) +"MB")
        return int((total_mem /1024)/1024)
    
    def get_container_id_pid_dict(self, name):
        containers_info_list = self.docker_opers.containers()
        id = ""
        for container_info in containers_info_list:
            container_name = container_info["Names"][0] 
            if container_name == name:
                id = container_info["Id"]
                break
            
        id_pid_dict = self.get_container_id_pid(id)
        return id_pid_dict
    
    
    def get_container_disk_load(self, name = ""):
        #docker_c = docker.Client(base_url = 'unix://var/run/docker.sock')
      
        
        invokeCmd = InvokeCommand()
        # _shell = options.pid_children + " " + str(ppid)
        _shell = "iotop -b -p%s -n2" % (str(self.id_pid_dict["pid_0"]))
        
        ret = invokeCmd._runSysCmd(_shell)
        pid_str = ret[0]
        
        pid_list = pid_str.strip().split()
        t_r_w_load = 0.0
        cmd_index = [item for item in range(len(pid_list)) if pid_list[item] == 'COMMAND']
        
        
        relative_p = cmd_index[-1]
        read_disk_load = pid_list[relative_p + 4]
        r_unit_str = pid_list[relative_p + 5]
        if "B" in r_unit_str:
            read_disk_load = float(read_disk_load) / 1024
        write_disk_load = pid_list[relative_p + 6]
        
        w_unit_str = pid_list[relative_p + 7]
        if "B" in w_unit_str:
            write_disk_load = float(write_disk_load) / 1024
           
        pid_load_dict = {}
            
        r_w_load = float(read_disk_load) + float(write_disk_load)
        t_r_w_load += r_w_load
        
        pid_load_dict.setdefault("pid_0", self.id_pid_dict["pid_0"])
        pid_load_dict.setdefault("r_w_load_0", r_w_load)
        self._logger.info("container_rw_load :" + str(pid_load_dict))
        
        pid = self.id_pid_dict["pid_0"]
        children_pid_list = self.get_container_children_pid(pid)
        
        suffix = 1
        for child in children_pid_list:
            
            _shell = "iotop -b -p%s -n2" % (str(child))
            ret = invokeCmd._runSysCmd(_shell)
            pid_str = ret[0]

            pid_list = pid_str.strip().split()
            cmd_index = [item for item in range(len(pid_list)) if pid_list[item] == 'COMMAND']
    
            relative_p = cmd_index[-1]
#             print pid_list
#             print "relative_p :" , relative_p
            if len(pid_list) >= relative_p + 4:
                read_disk_load = float(pid_list[relative_p + 4])
                r_unit_str = pid_list[relative_p + 5]
                if "B" in r_unit_str:
                    read_disk_load /= 1024
                    
                write_disk_load = float(pid_list[relative_p + 6])
                w_unit_str = pid_list[relative_p + 7]
                if "B" in w_unit_str:
                    write_disk_load /= 1024
                r_w_load = read_disk_load + write_disk_load
            else:
                r_w_load = 0.0
            
#             print "container process read_disk_load: %s" % (pid_list[24])
#             print "container process write_disk_load %s "% (pid_list[26])
#             
            pid_name = "pid_%s" % str(suffix)
            r_w_load_name = "r_w_load_%s" % str(suffix)
            
            pid_load_dict.setdefault(pid_name, str(child))
            pid_load_dict.setdefault(r_w_load_name, r_w_load)

            print r_w_load
            t_r_w_load += r_w_load
            suffix += 1
          
        pid_load_dict.setdefault("total", t_r_w_load)
        container_load = {}
        self._logger.info("all_pids_load_dict_dict :" + str(pid_load_dict))
        
        container_load.setdefault("total ", t_r_w_load)
        return container_load
#         pid_list2 = ret = invokeCmd._runSysCmd(_shell)
#         pid_str = ret[0]
#         pid_list2 = pid_str.strip().split()
#         sum2 = int(pid_list2[0]) + int (pid_list2[1])
#         
#         print "network workload: %s Bytes/s"  % (sum2 - sum1)
#    
    def get_container_cpu_load(self):
        percent = 0.0

        pid = self.id_pid_dict["pid_0"]
        
        pid_path = "/proc/%s/stat" % str(pid)
        f = open(pid_path, "r")
        lines = f.readlines()
        
        for line in lines:
            pid_list = line.split()
            pid_sum1 = int(pid_list[14]) + int(pid_list[15])
            
        f.close()
        
        sys_path = "/proc/stat"
        f = open(sys_path, "r")
        lines = f.readlines()
        for line in lines:
            sys_list = line.split()
            print sys_list
            sys_sum1 = int(sys_list[1]) + int (sys_list[3])
            break
        f.close()
        
        time.sleep(0.1)
        
        f = open(pid_path, "r")
        lines = f.readlines()
        
        for line in lines:
            pid_list = line.split()
            pid_sum2 = int(pid_list[14]) + int(pid_list[15])
        f.close()

        sys_path = "/proc/stat"
        f = open(sys_path, "r")
        lines = f.readlines()
        for line in lines:
            sys_list = line.split()
            sys_sum2 = int(sys_list[1]) + int (sys_list[3])
            break
        f.close()
        
        percent += float(pid_sum2 - pid_sum1) / float(sys_sum2 - sys_sum1)
        
        #pid = 1
        self._logger.info("Container's cpu usage is :" + str(percent))
        children_pid_list = self.get_container_children_pid(pid)
        
        for child in children_pid_list:
            pid_path = "/proc/%s/stat" % str(child)
            try:
                f = open(pid_path, "r")
                lines = f.readlines()
                for line in lines:
                    pid_list = line.split()
                    pid_sum1 = int(pid_list[14]) + int(pid_list[15])
                    #f.close()
            except IOError, e:
                continue
            finally:
                f.close()

            sys_path = "/proc/stat"
            f = open(sys_path, "r")
            lines = f.readlines()
            for line in lines:
                sys_list = line.split()
                sys_sum1 = int(sys_list[1]) + int (sys_list[3])
                break
            f.close()
        
            time.sleep(0.1)
        
            try:
                f = open(pid_path, "r")
                lines = f.readlines()
                for line in lines:
                    pid_list = line.split()
                    pid_sum2 = int(pid_list[14]) + int(pid_list[15])
                    f.close()
            except IOError, e:
                pid_sum2 = pid_sum1

            sys_path = "/proc/stat"
            f = open(sys_path, "r")
            lines = f.readlines()
            for line in lines:
                sys_list = line.split()
                sys_sum2 = int(sys_list[1]) + int(sys_list[3])
                break
            f.close()

            # print "value : %s" % str(float(pid_sum2 - pid_sum1) / float(sys_sum2 - sys_sum1))
            _percent = float(pid_sum2 - pid_sum1) / float(sys_sum2 - sys_sum1)  
            self._logger.info("%s process occupy %s " % (str(child), str(_percent)))
            percent += _percent
        self._logger.info("container occupy %s " % str(percent))     
        return percent
    
    def get_container_cpu_mem_load(self):
        pid = self.id_pid_dict["pid_0"]
        
        info_set = self.search_pid_family_info(pid)
        return info_set
        
    def get_container_network_load(self):
        
        pid = self.id_pid_dict["pid_0"]
        #_path = self.get_proc_net_path(pid)
        
        total_network_load = 0
        
        invokeCmd = InvokeCommand()
        # _shell = options.pid_children + " " + str(ppid)
        _shell = """cat /proc/%s/net/netstat | grep 'IpExt: ' | tail -n 1 | awk '{ print $8 "\t" $9 }'""" % str(pid)
        
        ret = invokeCmd._runSysCmd(_shell)
        pid_str = ret[0]
        pid_list1 = pid_str.strip().split()
        sum1 = sum2 = 0
        if pid_list1[0] != "cat:":
            sum1 = int(pid_list1[0]) + int(pid_list1[1])
        
            time.sleep(0.1)
            
            ret = invokeCmd._runSysCmd(_shell)
            pid_str = ret[0]
            pid_list2 = pid_str.strip().split()
            
            if pid_list2[0] != "cat:":
                
                sum2 = int(pid_list2[0]) + int (pid_list2[1])
            else:
                sum2 = sum1
                
        total_network_load += sum2 - sum1
        pid = self.id_pid_dict["pid_0"]
        children_pid_list = self.get_container_children_pid(pid)
        
        self._logger.info("container process occupy %s network load" % (total_network_load))
        for child in children_pid_list:
            _shell = """cat /proc/%s/net/netstat | grep 'IpExt: ' | tail -n 1 | awk '{ print $8 "\t" $9 }'""" % (str(child))
            ret = invokeCmd._runSysCmd(_shell)
            pid_str = ret[0]
            
            pid_list1 = pid_str.strip().split()
            sum1 = sum2 = 0
            if pid_list1[0] != "cat:":
                sum1 = int(pid_list1[0]) + int(pid_list1[1])
        
                time.sleep(0.1)
            
                ret = invokeCmd._runSysCmd(_shell)
                pid_str = ret[0]
                pid_list2 = pid_str.strip().split()
            
                if pid_list2[0] != "cat:":
                
                    sum2 = int(pid_list2[0]) + int (pid_list2[1])
                else:
                    sum2 = sum1
                
                self._logger.info("%s network load %sBytes" % (str(child), str(sum2 - sum1)))
                total_network_load += sum2 - sum1
            
        return total_network_load
        
    def get_container_alloc_mem(self):
        #docker_c = docker.Client(base_url = 'unix://var/run/docker.sock')
        containers_info_list = self.docker_opers.containers()
        id = ""
        mem = 0
        #print "containers_id_listcat /proc/39965/net/netstat | grep 'IpExt: ' | tail -n 1 | awk '{ print $8 "\t" $9 }' :" , containers_info_list
        if self.name != "":
            for container_info in containers_info_list:
                if self.name == container_info["Names"][0]:
                    id = container_info["Id"]
                    break
            mem = self.docker_c.inspect_container(id)['Config']['Memory']
        else:
            for container_info in containers_info_list:
                id = container_info["Id"]
                mem += self.docker_c.inspect_container(id)['Config']['Memory']
        self._logger.info("Memory allocated for Container is %s" % (str(mem)))
        return mem
        
    def get_proc_stat_path(self, pid):
        _path = "/proc/%s/stat" % (str(pid))
        return _path
    
    def get_proc_net_path(self, pid):
        _path = "/proc/%s/net/netstat" % (str(pid))
        return _path
        
    def get_page_size(self):
        _path = "/proc/meminfo"
        f = open(_path, "r")
        lines = f.readlines()

        mapped_size = 0
        for line in lines:
            list = line.split(":")
            if list[0] == "Mapped":
                mapped_size = int(list[1].strip().replace("kB",""))
                break
        f.close()

        _path = "/proc/vmstat"
        f = open(_path, "r")
        lines = f.readlines()
        
        # print lines
        nr_mapped = 0
        for line in lines:
            list = line.split(" ")
            if list[0] == "nr_mapped":
                nr_mapped= int(list[1].rstrip())
                break
        f.close()
        self._logger.info("Page size is %s" % str(mapped_size/nr_mapped))
        return mapped_size / nr_mapped   
    
    
    def container_occupy_mem_resource(self, name):
        containers_info_list = self.docker_opers.containers()
        id = ""
        # print "containers_id_list :" , containers_info_list
        container_names = containers_info_list[0]["Names"]
        for container_name in container_names:
            if container_name == name:
                id = containers_info_list[0]["Id"]
                break
             
#             print container_id_iter
        container_cur_rss = 0
        info_dict = self.get_container_id_pid(id)
        path = self.get_proc_stat_path(info_dict["pid_0"])
        
        pid = info_dict["pid_0"]
        f = open(path, "r")
        lines = f.readlines()
        for line in lines:
            pid_list = line.split()
            rss_mm = pid_list[23]
            container_cur_rss += int(rss_mm)
        #pid = 1    
        self._logger.info("Container process occupy %s pages" %(str(container_cur_rss)))  
        children_pid_list = self.get_container_children_pid(pid)
        
        for _pid in children_pid_list:
            path = self.get_proc_stat_path(int(_pid.rstrip()))
            f = open(path, "r")
            lines = f.readlines()
            for line in lines:
                pid_list = line.split()
                rss_mm = pid_list[23]
                container_cur_rss += int(rss_mm)
            
        page_size = self.get_page_size()
        
#         print "size is :", container_cur_rss * page_size
        self._logger.info("Container occupy %s KB" %(str(container_cur_rss * page_size)))
        return container_cur_rss * page_size    
        
    
    def containers_group_resource(self):
        
        _len = len(self.id_pid_dict)
        i = 0
        containers_cur_rss = 0
        for i in xrange(_len / 2 ):
            global container_cur_rss
            index = "pid_%s" % (0 + 2 * i)
            pid = self.id_pid_dict[index]
            path = self.get_proc_stat_path(pid)
            f = open(path, "r")
            lines = f.readlines()
            for line in lines:
                pid_list = line.split()
                rss_mm = pid_list[23]
                containers_cur_rss += int(rss_mm)
            
            children_pid_list = self.get_container_children_pid(pid)  

            for _pid in children_pid_list:
                path = self.get_proc_stat_path(int(_pid.rstrip()))
                f = open(path, "r")
                lines = f.readlines()
                for line in lines:
                    pid_list = line.split()
                    rss_mm = pid_list[23]
                    containers_cur_rss += int(rss_mm)
        page_size = self.get_page_size()
        
        self._logger.info("Host containers occupy %s KB Memory" % str(containers_cur_rss * page_size))
        return containers_cur_rss * page_size
        
    
    def get_container_id_pid(self, id):
        id_pid_dict = {}
                  
        id_pid_dict.setdefault("container_id_0", id)
        pid = self.docker_c.inspect_container(id)['State']['Pid']
        id_pid_dict.setdefault("pid_0", pid)
        
        self._logger.info("container_id : id" + str(id_pid_dict))
        return id_pid_dict
            
    def get_containers_id_pid(self):
        containers_id_list = self.docker_opers.retrieve_containers_ids()
        id_pid_dict = {}
        i = 0
        for container_id_iter in containers_id_list:
            container_id = "container_id_%s " % i
            id_pid_dict.setdefault(container_id, container_id_iter)
            pid = self.docker_c.inspect_container(container_id_iter)['State']['Pid']
            pid_index = "pid_%s" % i
            id_pid_dict.setdefault(pid_index, pid)
            i += 1
        
        self._logger.info("containers_id : id" + str(id_pid_dict))
#         print id_pid_dict
        return id_pid_dict
    
    def get_container_children_pid(self, ppid = 1):
        invokeCmd = InvokeCommand()
        _shell = 'shell/list_children.sh %s' % ppid
        ret = invokeCmd._runSysCmd(_shell)
        pid_str = ret[0]
        pid_list =pid_str.strip().split()
        self._logger.info("%s children pid: %s" % (ppid, str(pid_list)))
        
        
        return pid_list
    
    
    def memory_stat(self):  
        mem, stat = {}, {} 
        f = open("/proc/meminfo", "r")  
        lines = f.readlines()  
        f.close()
        for line in lines:  
            if len(line) < 2: continue  
            name = line.split(':')[0]  
            var = line.split(':')[1].split()[0]  
            mem[name] = long(var) * 1024.0  
        stat['total'] = int(mem['MemTotal']/(1024*1024))
        stat['used'] = int(mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached'])/(1024*1024)
        stat['free'] = int(mem['MemFree'] + mem['Buffers'] + mem['Cached'])/(1024*1024)
        self._logger.info("Memory stat : "  + str(stat))
        return stat

    def disk_stat(self):
        """
        just for container
        """
        hd={}
        disk = os.statvfs("/srv")
        hd['free'] = disk.f_bsize * disk.f_bavail / (1024*1024)
        hd['total'] = disk.f_bsize * disk.f_blocks / (1024*1024)
        hd['used'] = hd['total'] - hd['free']
        self._logger.info("hard disk stat :" + str(hd))
        return hd
   
    def disk_loadavg(self):  
        loadavg = {}  
        f = open("/proc/loadavg", "r")  
        con = f.read().split()
        f.close()  
        loadavg['lavg_1']=con[0]  
        loadavg['lavg_5']=con[1]  
        loadavg['lavg_15']=con[2]  
        loadavg['nr']=con[3]  
        loadavg['last_pid']=con[4]  
        self._logger.info("disk io information: " + str(loadavg)) 
        return loadavg

    def get_dev_name(self):
        invokeCmd = InvokeCommand()
        _shell = "df -h"
        ret_sub_p = invokeCmd._runSysCmd(_shell)
        contents_list = ret_sub_p[0].split()
        self._logger.info(str(contents_list))
        srv_index = contents_list.index("/srv")

        dev_name = contents_list[srv_index - 5]
        self._logger.info(str(dev_name))
        
        return dev_name
   
    def disk_instant_load(self):
        mount_dev = self.get_dev_name()
        invokeCmd = InvokeCommand()
        _shell = "iostat -dxk %s 2 2" % (mount_dev)
        self._logger.info(str(_shell))
        ret_sub_p = invokeCmd._runSysCmd(_shell)
        contents_list =  ret_sub_p[0].split()
        w_kb_s = float(contents_list[-6])
        r_kb_s = float(contents_list[-7])
        per_kb_s = (w_kb_s + r_kb_s) 
        return per_kb_s

    def cpu_info(self):  
        cpu = []  
        cpuinfo = {}  
        f = open("/proc/cpuinfo", "r")
        lines = f.readlines() 
        f.close()  
        for line in lines:  
            if line == '\n':  
                cpu.append(cpuinfo)  
                cpuinfo = {}  
            if len(line) < 2: 
                continue  
            name = line.split(':')[0].rstrip()  
            var = line.split(':')[1].rstrip()
            cpuinfo[name] = var 
        self._logger.info("cpu information :" + str(cpu))
        return cpu
    
    def _read_network_statics(self):
        """Read the current network statics from /proc/net/dev """
        try:
            fd = open("/proc/net/dev", "r")
            lines = fd.readlines()
        finally:
            if fd:
                fd.close()
        sum1 = 0.0
        for line in lines:
            list = line.split(':')
            if len(list) == 1:
                continue
            sum1 += long(list[1].split()[0])
            sum1 += long(list[1].split()[8])
        return sum1   
      
    def get_top_cmd_ret(self):
        invokeCmd = InvokeCommand()
        # _shell = options.pid_children + " " + str(ppid)
        _shell = "top -b -n1 |sort -n " 
        
        ret = invokeCmd._runSysCmd(_shell)
        set_str = ret[0]
        #print set_str
        set_list = set_str.split()
        #print set_list
        ave_p = [item for item in range(len(set_list)) if set_list[item] == 'average:']
        start_p = ave_p[0] + 4
        #print set_list[start_p]
        
        top_matrix_list = list(set_list[start_p:])
        #print matrix_list
        #print len(matrix_list)
        return top_matrix_list
    
    def search_pid_family_info(self, pid = 1):
        children_pid_list = self.get_container_children_pid(pid)
        rss_mm = 0.0
        cpu_percent = 0.0
        
        info_dict = {}
        info_dict = (self.search_pid_info(int(pid)))
        rss_mm += info_dict["pid_rss_memory"]
        cpu_percent += info_dict["pid_cpu_usage"]
       
        for child in children_pid_list:
            #print self.search_pid_info(int(child))
            info_dict = (self.search_pid_info(int(child)))
            if info_dict != None:
                rss_mm += info_dict["pid_rss_memory"]
                cpu_percent += info_dict["pid_cpu_usage"]
            else:
                pass
            
        dict = {}
        dict.setdefault("total_rss", rss_mm)
        dict.setdefault("total_cpu_percent", cpu_percent)
        return dict
    
    def search_pid_info(self, pid = 1):
        N = 12
        group_n = len(self.matrix_list) / 12
        
        start = 0
        middle = group_n / 2
        end = group_n - 1
        
        while (pid != int(self.matrix_list[middle * N]) and (middle != start) and (middle != end)):
            if pid < int(self.matrix_list[middle * N]):
                end = middle
                middle = (start + middle) / 2
                
            else:
                start = middle
                middle = (middle + end) / 2
                    
        if pid != int(self.matrix_list[middle * N]):
            pass             
        else:
            dict = {}

            name = "pid_%s" % str(pid)
            dict.setdefault(name, pid)
            str_rss = self.matrix_list[middle * N + 5]
            if "m" in str_rss:
                _rss = str_rss.replace("m","")
                str_rss = str(float(_rss) * 1024)
            dict.setdefault("pid_rss_memory", float(str_rss))
            dict.setdefault ("pid_cpu_usage", float(self.matrix_list[middle * N + 8]))
                        
            return  dict
    
    def get_cur_cpu_usage(self):
        invokeCmd = InvokeCommand()
        _shell = "vmstat 1 2"
        ret = invokeCmd._runSysCmd(_shell)
        pid_str = ret[0]
        pid_list = pid_str.strip().split()
        id =  pid_list[-3]
        return id
        
    def get_cur_net_load(self):
        """
        get net average statics of work load in 2 seconds
        """
        n1 = self._read_network_statics()
        time.sleep(0.1)
        n2 = self._read_network_statics()
        avg_load = (n2 - n1) / 1024
        self._logger.info("network load per second at this time:" + str(avg_load))
        return avg_load
