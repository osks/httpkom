# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

from pylyskom.komsession import KomSession


def _get_exposed_komsession_methods(hidden_methods):
    exposed = []
    for attr_name in dir(KomSession):
        if attr_name in hidden_methods:
            continue
        if attr_name.startswith('_'):
            # skip "private" methods/variables
            continue
        if not callable(getattr(KomSession, attr_name)):
            # skip variables
            continue
        exposed.append(attr_name)
    return exposed


_hidden_komsession_methods = []

EXPOSED_KOMSESSION_METHODS = _get_exposed_komsession_methods(_hidden_komsession_methods)
