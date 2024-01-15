#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from typing import Any

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
    def redis(self) -> Redis:  # type: ignore[type-arg]
        return Redis(connection_pool=self.redis_pool)

    def check_redis_up(self) -> bool:
        return self.redis.ping()

    def info(self) -> dict[str, Any]:
        return {
            "expire_urls": get_config('generic', 'expire_urls'),
            "dump_fetch_frequency": get_config('generic', 'dump_fetch_frequency'),
            "unique_urls": self.redis.zcard('urls'),
            "unique_ccs": self.redis.zcard('ccs'),
            "unique_asns": self.redis.zcard('asns'),
            "unique_ips": self.redis.zcard('ips')
        }

    def get_url_entry(self, url: str) -> dict[str, Any] | None:
        entry = self.redis.hgetall(url)
        if not entry:
            return None
        entry['details'] = json.loads(entry['details'])
        return entry

    def get_ips(self) -> list[str] | None:
        return self.redis.zrangebyscore('ips', '-Inf', '+Inf')

    def get_asns(self) -> list[str] | None:
        return self.redis.zrangebyscore('asns', '-Inf', '+Inf')

    def get_ccs(self) -> list[str] | None:
        return self.redis.zrangebyscore('ccs', '-Inf', '+Inf')

    def get_urls(self) -> list[str] | None:
        return self.redis.zrangebyscore('urls', '-Inf', '+Inf')

    def get_urls_by_ip(self, ip: str) -> list[str] | None:
        return self.redis.zrangebyscore(ip, '-Inf', '+Inf')

    def get_urls_by_asn(self, asn: str) -> list[str] | None:
        return self.redis.zrangebyscore(asn, '-Inf', '+Inf')

    def get_urls_by_cc(self, cc: str) -> list[str] | None:
        return self.redis.zrangebyscore(cc, '-Inf', '+Inf')
