#!/usr/bin/env python3

from __future__ import annotations

from subprocess import Popen, run

from phishtank.default import get_homedir


def main() -> None:
    # Just fail if the env isn't set.
    get_homedir()
    print('Start backend (redis)...')
    p = run(['run_backend', '--start'])
    p.check_returncode()
    print('done.')
    print('Start import process...')
    Popen(['importer'])
    print('done.')
    print('Start website...')
    Popen(['start_website'])
    print('done.')


if __name__ == '__main__':
    main()
