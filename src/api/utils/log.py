#!/usr/bin/env python
#-*- coding: utf-8 -*-
import logging


def _log_docker_run_command(docker_model):
        
        cmd = ''
        cmd += 'docker run -i -t --rm --privileged -n --memory="%s" -h %s'  % (docker_model.mem_limit, docker_model.name)
        _volumes = docker_model.volumes
        if _volumes:
            for host_addr, container_addr in _volumes.items():
                if container_addr:
                    cmd += ' -v %s:%s \n' % (host_addr, container_addr)
                else:
                    cmd += ' -v %s \n' % host_addr
        
        env = docker_model.environment
        if env:
            cmd += '--env "ZKID=%s" \n' % env.get('ZKID')
            cmd += '--env "IP=%s" \n' % env.get('IP')
            cmd += '--env "HOSTNAME=%s" \n' % env.get('HOSTNAME')
            cmd += '--env "NETMASK=%s" \n' % env.get('NETMASK')
            cmd += '--env "GATEWAY=%s" \n' % env.get('GATEWAY')
            N1_IP = env.get('N1_IP')
            if N1_IP:
                cmd += '--env "N1_IP=%s" \n' % N1_IP
            N1_HOSTNAME = env.get('N1_HOSTNAME')
            if N1_HOSTNAME:
                cmd += '--env "N1_HOSTNAME=%s" \n' % N1_HOSTNAME
            N2_IP = env.get('N2_IP')
            if N2_IP:
                cmd += '--env "N2_IP=%s" \n' % N2_IP
            N2_HOSTNAME = env.get('N2_HOSTNAME')
            if N2_HOSTNAME:
                cmd += '--env "N2_HOSTNAME=%s" \n' % N2_HOSTNAME 
            N3_IP = env.get('N3_IP')
            if N3_IP:
                cmd += '--env "N3_IP=%s" \n' % N3_IP 
            N3_HOSTNAME = env.get('N3_HOSTNAME')
            if N3_HOSTNAME:
                cmd += '--env "N3_HOSTNAME=%s" \n' % N3_HOSTNAME 
        cmd += '--name %s %s' % (docker_model.name, docker_model.image)
        logging.info(cmd)