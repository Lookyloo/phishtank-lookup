#!/usr/bin/env python3

import time

from phishtank.default import AbstractManager


def main() -> None:
    AbstractManager.force_shutdown()
    time.sleep(5)
    while True:
        try:
            running = AbstractManager.is_running()
        except FileNotFoundError:
            print('Redis is already down.')
            break
        if not running:
            break
        print(running)
        time.sleep(5)


if __name__ == '__main__':
    main()
