#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import Optional, Dict

from redis import ConnectionPool, Redis
from redis.connection import UnixDomainSocketConnection

from .default import get_config, get_socket_path


class Phishtank():

    def __init__(self) -> None:
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.logger.setLevel(get_config('generic', 'loglevel'))

        self.redis_pool: ConnectionPool = ConnectionPool(connection_class=UnixDomainSocketConnection,
                                                         path=get_socket_path('cache'), decode_responses=True)

    @property
    def redis(self):
        return Redis(connection_pool=self.redis_pool)

    def info(self):
        return {
            "expire_urls": get_config('generic', 'expire_urls'),
            "dump_fetch_frequency": get_config('generic', 'dump_fetch_frequency'),
            "unique_urls": self.redis.zcard('urls'),
            "unique_ccs": self.redis.zcard('ccs'),
            "unique_asns": self.redis.zcard('asns'),
            "unique_ips": self.redis.zcard('ips')
        }

    def get_url_entry(self, url: str) -> Optional[Dict]:
        entry = self.redis.hgetall(url)
        if not entry:
            return None
        entry['details'] = json.loads(entry['details'])
        return entry

    def get_ips(self) -> Optional[str]:
        return self.redis.zrangebyscore('ips', '-Inf', '+Inf')

    def get_asns(self) -> Optional[str]:
        return self.redis.zrangebyscore('asns', '-Inf', '+Inf')

    def get_ccs(self) -> Optional[str]:
        return self.redis.zrangebyscore('ccs', '-Inf', '+Inf')

    def get_urls(self) -> Optional[str]:
        return self.redis.zrangebyscore('urls', '-Inf', '+Inf')

    def get_urls_by_ip(self, ip: str) -> Optional[str]:
        return self.redis.zrangebyscore(ip, '-Inf', '+Inf')

    def get_urls_by_asn(self, asn: str) -> Optional[str]:
        return self.redis.zrangebyscore(asn, '-Inf', '+Inf')

    def get_urls_by_cc(self, cc: str) -> Optional[str]:
        return self.redis.zrangebyscore(cc, '-Inf', '+Inf')
