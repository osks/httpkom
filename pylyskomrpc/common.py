# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

from pylyskom.komsession import KomSession
from .komgevent import GeventKomSession


def _get_public_methods(cls, hidden_methods):
    exposed = []
    for attr_name in dir(cls):
        if attr_name in hidden_methods:
            continue
        if attr_name.startswith('_'):
            # skip "private" methods/variables
            continue
        if not callable(getattr(cls, attr_name)):
            # skip variables
            continue
        exposed.append(attr_name)
    return exposed


_hidden_methods = []

EXPOSED_KOMSESSION_METHODS = _get_public_methods(KomSession, _hidden_methods)
EXPOSED_KOMSESSION_METHODS.extend(_get_public_methods(GeventKomSession, _hidden_methods))
