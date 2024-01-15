#!/usr/bin/env python3

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from .default import get_homedir, safe_create_dir


# This method is used in json.dump or json.dumps calls as the default parameter:
# json.dumps(..., default=dump_to_json)
def serialize_to_json(obj: set[Any]) -> list[Any]:
    if isinstance(obj, set):
        return list(obj)


@lru_cache(64)
def get_data_dir() -> Path:
    capture_dir = get_homedir() / 'data'
    safe_create_dir(capture_dir)
    return capture_dir
