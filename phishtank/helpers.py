#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Union

from .default import get_homedir, safe_create_dir


# This method is used in json.dump or json.dumps calls as the default parameter:
# json.dumps(..., default=dump_to_json)
def serialize_to_json(obj: Union[Set]) -> Union[List]:
    if isinstance(obj, set):
        return list(obj)


@lru_cache(64)
def get_data_dir() -> Path:
    capture_dir = get_homedir() / 'data'
    safe_create_dir(capture_dir)
    return capture_dir
