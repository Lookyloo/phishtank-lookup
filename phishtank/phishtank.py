#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Optional, Dict

from redis import ConnectionPool, Redis
from redis.connection import UnixDomainSocketConnection

# from .exceptions import PhishtankException

from .helpers import get_config, get_socket_path


class Phishtank():

    def __init__(self) -> None:
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.logger.setLevel(get_config('generic', 'loglevel'))

        self.redis_pool: ConnectionPool = ConnectionPool(connection_class=UnixDomainSocketConnection,
                                                         path=get_socket_path('cache'), decode_responses=True)

    @property
    def redis(self):
        return Redis(connection_pool=self.redis_pool)

    def get_url_entry(self, url: str) -> Optional[Dict]:
        return self.redis.hgetall(url)
