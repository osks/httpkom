# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging
import uuid

from pylyskom.komsession import KomSession


logger = logging.getLogger()


def _new_komsession_id():
    return str(uuid.uuid4())


class KomSessionStorage(object):
    def __init__(self, komsession_factory=KomSession):
        self._komsession_factory = komsession_factory
        self._komsessions = dict()

    def new(self, host, port):
        assert host is not None
        assert port is not None
        komsession_id = _new_komsession_id()
        assert komsession_id not in self._komsessions
        self._komsessions[komsession_id] = self._komsession_factory(host, port)
        return komsession_id
    
    def remove(self, komsession_id):
        assert komsession_id is not None
        if self.has(komsession_id):
            del self._komsessions[komsession_id]
            return True
        return False

    def has(self, komsession_id):
        return komsession_id in self._komsessions

    def get(self, komsession_id):
        assert komsession_id is not None
        return self._komsessions[komsession_id]
