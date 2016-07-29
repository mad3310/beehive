#coding=utf-8
from esOpers import esOpers
import datetime

class ServerRes(object):
    ALL_RES = {
                'memory' : {
                             'index_prefix':'monitor_server_resource_memory',
                             'time_interval' : 600,
                             'doc_type' : 'memory',
                             'size' : 200,
                             'field': 'free'
                           },
                'diskusage' : {
                                 'index_prefix':'monitor_server_resource_diskusage',
                                 'time_interval' : 600,
                                 'doc_type' : 'diskusage',
                                 'size' : 200,
                                 'field': 'used,total'
                               },
                'container_count' : {
                             'index_prefix':'monitor_server_resource_container_count',
                             'time_interval' : 600,
                             'doc_type' : 'container_count',
                             'size' : 200,
                             'field': 'container_count'
                        },
                'diskiops' : {
                                 'index_prefix':'monitor_server_resource_diskiops',
                                 'time_interval' : 600,
                                 'doc_type' : 'diskiops',
                                 'size' : 200,
                                 'field': 'read_iops,write_iops'
                            },
             }

    def __init__(self):
        self.esOper = esOpers()

    def connect(self, es_hosts):
        self.esOper.connect(es_hosts)

    def _get_index_name(self, prefix, timestart):
        suffix = timestart.strftime('%Y%m%d')
        return '%s_%s' %(prefix,suffix)

    def _retrieve_time_range(self, time_interval):
        now = datetime.datetime.utcnow()
        today = now.strftime('%Y-%m-%d')
        before = now-datetime.timedelta(seconds=time_interval)
        if today != before.strftime('%Y-%m-%d'):
            mid = datetime.datetime.strptime(today, '%Y-%m-%d')
            yield before, mid
            yield mid, now 
        else:
            yield before, now

    def _retireve_server_resoure_list(self, ip, res_type):
        time_interval = self.ALL_RES[res_type]['time_interval']
        prefix = self.ALL_RES[res_type]['index_prefix']
        doc_type = self.ALL_RES[res_type]['doc_type'] 
        size = self.ALL_RES[res_type]['size']
        res = []
        for start, end in self._retrieve_time_range(time_interval):
            index = self._get_index_name(prefix, start)
            _res = self.esOper.get_all_source(index, ip, start, end,
                                              doc_type, size)
            res.extend(_res)
        return res
   
    def retireve_server_resource(self, ip, res_type):
        resources = self._retireve_server_resoure_list(ip, res_type)
        length = len(resources)
        fields = self.ALL_RES[res_type]['field'].split(',')
        ret = {}
        map(lambda x:ret.update({x:0}), fields)
        if not length:
            return ret 
        for field in fields:
            _tmp = sum(map(lambda x: x[field], resources))/length
            ret[field] = _tmp
        return ret

    def retireve_server_memory(self, ip):
        return self.retireve_server_resource(ip, 'memory')

    def retireve_server_diskusage(self, ip):
        return self.retireve_server_resource(ip, 'diskusage')

    def retireve_server_container_number(self, ip):
        containers = self.retireve_server_resource(ip,
                        'container_count')
        return containers['container_count']

    def retireve_server_diskiops(self, ip):
        return self.retireve_server_resource(ip, 'diskiops')

ServerRes = ServerRes()

if __name__  == "__main__":
    es_hosts = '10.140.65.12:9200,10.140.65.13:9200,10.140.65.14:9200'
    ServerRes.connect(es_hosts)
    ip = '10.185.30.252'
    print ServerRes.retireve_server_memory(ip)
    print ServerRes.retireve_server_diskusage(ip)
    print ServerRes.retireve_server_container_number(ip)
    print ServerRes.retireve_server_diskiops(ip)

