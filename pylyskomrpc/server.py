# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import functools
import logging
import uuid

#import gevent
import zerorpc

from pylyskom import kom
from pylyskom.komsession import KomSession, KomSessionException

from httpkom.komserialization import to_dict

from common import EXPOSED_KOMSESSION_METHODS


logger = logging.getLogger(__name__)


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


# TODO: remove storage and inline it in KomSessionServer. It has so
# little functionality that having a separate class doesn't really
# give anything.

class KomSessionServer(object):
    def __init__(self, storage=None):
        if storage is None:
            storage = KomSessionStorage()

        self._storage = storage

    def create_session(self, host, port):
        return self._storage.new(host, port)

    def delete_session(self, komsession_id):
        if self._storage.has(komsession_id):
            # make sure the connection is closed before we remove it
            self._storage.get(komsession_id).close()
        return self._storage.remove(komsession_id)

    def has_session(self, komsession_id):
        return self._storage.has(komsession_id)

    def call_session(self, komsession_id, method_name, args, kwargs):
        if method_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("Session has no method called %r" % (method_name,))

        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
    
        # todo: un-dict arguments?

        komsession = self._storage.get(komsession_id)
    
        result_dict = None
        error_dict = None
        try:
            result = getattr(komsession, method_name)(*args, **kwargs)
            result_dict = to_dict(result, True, komsession)
        except KomSessionException as ex:
            error_dict = dict(
                type='komsession',
                class_name=ex.__class__.__name__,
                args=ex.args)
        except kom.Error as ex:
            error_dict = dict(
                type='kom',
                class_name=ex.__class__.__name__,
                args=ex.args)
    
        return result_dict, error_dict



#class GeventKomSession(KomSession):
#    pass


#def test():
#    while True:
#        print "hej"
#        gevent.sleep(1)


#gevent.spawn(test)


def run_session_server():
    logger.info("Starting")
    session_server = KomSessionServer()
    rpcserver = zerorpc.Server(session_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()
