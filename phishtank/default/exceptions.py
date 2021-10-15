#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class PhishtankException(Exception):
    pass


class MissingEnv(PhishtankException):
    pass


class CreateDirectoryException(PhishtankException):
    pass


class ConfigError(PhishtankException):
    pass
