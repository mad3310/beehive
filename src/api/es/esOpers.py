#coding=utf-8
from elasticsearch import Elasticsearch
import logging
import datetime

class esOpers(object):

    def __init__(self):
        self.es = None

    def connect(self, es_host):
        hosts = map(lambda x:dict(host=x.split(':')[0],
                                port=x.split(':')[1]),
                     es_host.split(','),
                   ) 
        if not self.es:
            self.es = Elasticsearch(
                            hosts,
                            sniff_on_start=False,
                            sniff_on_connection_fail=True,
                            sniffer_timeout=300,
                            sniff_timeout=10,
                            )

    def get_all_source(self, index, ip, time_from, 
                       time_to, doc_type, size,
                       source_fields = []):
        res = self._get_all_values(index, ip, time_from, 
                             time_to, doc_type, size, source_fields)
        ret = []
        for _res in res:
            if _res.has_key('_source'):
                ret.append(_res['_source'])
        return ret

    def _query_body(self, ip, time_from, time_to, doc_type,
                    source_fields):
        range_field = '%s.timestamp' % doc_type
        ip_field = '%s.ip' % doc_type
        body = {
                   '_source': source_fields,
                   'query': 
                   {
                      'bool': 
                      {
                         'must': [
                           {
                             'range': 
                             {
                                 range_field: 
                                 {
                                     'from':time_from,
                                     'to':  time_to 
                                 }
                             },
                           },
                           {
                             'term':
                             {
                                 ip_field : ip 
                             }
                           }
                        ]
                      }
                   }
                }
        return body

    def _get_all_values(self, index, ip, time_from, time_to,
            doc_type, size, source_fields): 
        ret = []
        try:
            res = self.es.search(index = index, doc_type = doc_type, 
                  size = size, 
                  body = self._query_body(ip, time_from, time_to,
                            doc_type, source_fields))
            ret = res['hits']['hits']
        except Exception as e:
            logging.error("query in es fail\n%s" %e, exc_info=True)
        return ret

