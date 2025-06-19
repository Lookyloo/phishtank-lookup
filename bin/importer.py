#!/usr/bin/env python3

from __future__ import annotations

import gzip
import bz2
import json
import logging
import logging.config
import shutil

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote_plus

from redis import Redis
import requests

from phishtank.default import get_socket_path, get_config, AbstractManager
from phishtank.helpers import get_data_dir

logging.config.dictConfig(get_config('logging'))


class Importer(AbstractManager):

    def __init__(self, loglevel: int=logging.INFO):
        super().__init__(loglevel)
        self.script_name = 'importer'
        self.redis = Redis(unix_socket_path=get_socket_path('cache'))

        # make sure data dir exists
        self.data_dir = get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir_archive = get_data_dir() / 'archive'
        self.data_dir_archive.mkdir(parents=True, exist_ok=True)

        phishtank_api_key = get_config('generic', 'phishtank_api_key')
        self.expire_urls = get_config('generic', 'expire_urls')
        self.fetch_freq = get_config('generic', 'dump_fetch_frequency')
        self.useragent = get_config('generic', 'phishtank_useragent')

        if phishtank_api_key:
            self.json_db_url = f'https://data.phishtank.com/data/{phishtank_api_key}/online-valid.json.bz2'
        else:
            self.json_db_url = 'https://data.phishtank.com/data/online-valid.json.bz2'

    def _to_run_forever(self) -> None:
        if to_import := self._fetch():
            self._import(to_import)

    def _fetch(self) -> Path | None:
        for path in self.data_dir.iterdir():
            if path.is_file() and path.suffix == '.json':
                last_update = datetime.fromisoformat(path.stem)
                if last_update > datetime.now() - timedelta(hours=self.fetch_freq):
                    # The dump is generated once every hour.
                    self.logger.info(f'Interval not expired ({(last_update + timedelta(hours=1)).isoformat()}), not fetching.')
                    return None
                else:
                    self.logger.info('Interval expired, archive old file...')
                    dest_dir = self.data_dir_archive / f'{path.name}.gz'
                    with path.open('rb') as f_in:
                        with gzip.open(dest_dir, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    path.unlink()
                    self.logger.info('Archiving over.')

        # NOTE: In theory, one should be able to get the ETag header and know if the file was changed
        # but it's not a thing anymore.
        # response = requests.head(self.json_db_url)

        self.logger.info('Fetching new file...')
        headers = {'user-agent': self.useragent}
        response = requests.get(self.json_db_url, headers=headers)
        self.logger.info('Fetching done.')
        if content := response.content:
            if content[0] == 60:  # 60 is b'<'
                self.logger.error('Got the dumb JS page, will try again later...')
                return None

            try:
                json_response = json.loads(bz2.decompress(content))
            except Exception as e:
                self.logger.error(f'Error while reading bz2 file from {self.json_db_url}: {e}')
                return None
            dest_file = self.data_dir / f'{datetime.now().isoformat()}.json'
            with dest_file.open('w') as f:
                json.dump(json_response, f)
            return dest_file
        else:
            self.logger.error('JSON received from Phishtank is empty.')
            return None

    def _import(self, to_import: Path) -> None:
        '''Import a dump
            Keys in redis:
                * 'urls': the list of urls currently in the database - zrank to expire them
                * <url>: the URL from the dump, the complete entry - expire automatically
                * <ip>: the URLs associated to this IP - zrank to expire them and autoexpire
                * <ASN>: the URLs associated to this AS - zrank to expire them and autoexpire
                * <country>: the URLs associated to this CC - zrank to expire them an autoexpire
        '''
        with to_import.open() as f:
            self.logger.info('Importing new file...')
            expire_zranks = int((datetime.now() + timedelta(hours=self.expire_urls)).timestamp())
            # Make sure the urls aren't expired before the zranks are cleared up
            expire_in_sec = 3600 * (self.expire_urls + self.fetch_freq)

            urls: dict[str, dict[str, Any]] = {}
            ips: dict[str, list[str]] = defaultdict(list)
            asns: dict[str, list[str]] = defaultdict(list)
            country_codes: dict[str, list[str]] = defaultdict(list)

            for entry in json.load(f):
                entry['url'] = unquote_plus(entry['url'])

                for d in entry['details']:
                    ips[d['ip_address']].append(entry['url'])
                    asns[d['announcing_network']].append(entry['url'])
                    country_codes[d['country']].append(entry['url'])

                entry['details'] = json.dumps(entry['details'])
                urls[entry['url']] = entry

            p = self.redis.pipeline()
            zranks_to_expire = ['urls', 'ips', 'asns', 'ccs']
            p.zadd('urls', {url: expire_zranks for url in urls.keys()})
            for url, entry in urls.items():
                p.hmset(url, entry)  # type: ignore[arg-type]
                p.expire(url, expire_in_sec)

            p.zadd('ips', {ip: expire_zranks for ip in ips.keys()})
            for ip, _urls in ips.items():
                p.zadd(ip, {url: expire_zranks for url in _urls})
                p.expire(ip, expire_in_sec)
                zranks_to_expire.append(ip)

            p.zadd('asns', {asn: expire_zranks for asn in asns.keys()})
            for asn, _urls in asns.items():
                p.zadd(asn, {url: expire_zranks for url in _urls})
                p.expire(asn, expire_in_sec)
                zranks_to_expire.append(asn)

            p.zadd('ccs', {cc: expire_zranks for cc in country_codes.keys()})
            for cc, _urls in country_codes.items():
                p.zadd(cc, {url: expire_zranks for url in _urls})
                p.expire(cc, expire_in_sec)
                zranks_to_expire.append(cc)

            # Expire the keys we just updated
            for key in zranks_to_expire:
                p.zremrangebyscore(key, '-Inf', int(datetime.now().timestamp()))

            p.execute()
            self.logger.info('Importing done.')


def main() -> None:
    i = Importer()
    fetch_freq = get_config('generic', 'dump_fetch_frequency')
    i.run(sleep_in_sec=3600 * fetch_freq)


if __name__ == '__main__':
    main()
