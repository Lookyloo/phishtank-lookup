#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import unquote_plus

from redis import Redis
import requests

from phishtank.abstractmanager import AbstractManager
from phishtank.helpers import (get_data_dir, get_socket_path, get_config)

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s',
                    level=logging.INFO)


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

        if phishtank_api_key:
            self.json_db_url = f'https://data.phishtank.com/data/{phishtank_api_key}/online-valid.json'
        else:
            self.json_db_url = 'https://data.phishtank.com/data/online-valid.json'

    def _to_run_forever(self):
        if to_import := self._fetch():
            self._import(to_import)

    def _fetch(self) -> Optional[Path]:
        for path in self.data_dir.iterdir():
            if path.is_file() and path.suffix == '.json':
                last_update = datetime.fromisoformat(path.stem)
                if last_update > datetime.now() - timedelta(hours=1):
                    # The dump is generated once every hour.
                    self.logger.info(f'Interval not expired ({(last_update + timedelta(hours=1)).isoformat()}), not fetching.')
                    return
                else:
                    self.logger.info('Interval expired, archive old file...')
                    with path.open('rb') as f_in:
                        with gzip.open(f'{path}.gz', 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    path.unlink()
                    self.logger.info('Archiving over.')

        # NOTE: In theory, one should be able to get the ETag header and know if the file was changed
        # but it's not a thing anymore.
        # response = requests.head(self.json_db_url)

        self.logger.info('Fetching new file...')
        headers = {'user-agent': 'phishtank/phishtank-lookup (Lookyloo)'}
        response = requests.get(self.json_db_url, headers=headers)
        self.logger.info('Fetching done.')
        dest_file = self.data_dir / f'{datetime.now().isoformat()}.json'
        with dest_file.open('w') as f:
            json.dump(response.json(), f)
        return dest_file

    def _import(self, to_import: Path):
        '''Import a dump'''
        with to_import.open() as f:
            self.logger.info('Importing new file...')
            p = self.redis.pipeline()
            for entry in json.load(f):
                entry['url'] = unquote_plus(entry['url'])
                entry['details'] = json.dumps(entry['details'])
                p.hmset(entry['url'], entry)
                p.expire(entry['url'], 3600 * 48)
            p.execute()
            self.logger.info('Importing done.')


def main():
    i = Importer()
    i.run(sleep_in_sec=3600 * 1)


if __name__ == '__main__':
    main()
