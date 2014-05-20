# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging
import uuid

import gevent
import zerorpc

from pylyskom import kom
from pylyskom.komsession import KomSession, KomSessionException

from httpkom.komserialization import to_dict

from common import EXPOSED_KOMSESSION_METHODS


logger = logging.getLogger(__name__)


def _new_komsession_id():
    return str(uuid.uuid4())


# TODO: remove storage and inline it in KomSessionServer. It has so
# little functionality that having a separate class doesn't really
# give anything.

class KomSessionServer(object):
    def __init__(self, komsession_factory=KomSession):
        assert komsession_factory is not None
        self._komsession_factory = komsession_factory
        self._komsessions = dict()

    def create_session(self):
        komsession_id = _new_komsession_id()
        assert not self.has_session(komsession_id)
        self._komsessions[komsession_id] = self._komsession_factory()
        return komsession_id

    def delete_session(self, komsession_id):
        assert komsession_id is not None
        if komsession_id in self._komsessions:
            # make sure the connection is closed before we remove it
            del self._komsessions[komsession_id]
            return True
        return False

    def has_session(self, komsession_id):
        assert komsession_id is not None
        return komsession_id in self._komsessions

    def call_session(self, komsession_id, method_name, args, kwargs):
        assert self.has_session(komsession_id)
        komsession = self._komsessions[komsession_id]

        if method_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("Session has no method called %r" % (method_name,))

        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
    
        # todo: un-dict arguments?

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



class GeventKomSession(KomSession):
    def connect(self, host, port, username, hostname, client_name, client_version):
        KomSession.connect(self, host, port, username, hostname, client_name, client_version)
        self.add_async_handler()

    def add_async_handler(self):
        self._conn.add_async_handler(kom.ASYNC_NEW_TEXT, self._handle_async)
        
    def _handle_async(self, msg, c):
        logger.info("got async message")


def test():
    while True:
        logger.debug("test")
        gevent.sleep(2)

#gevent.spawn(test)

def create_komsession():
    return GeventKomSession()


def run_session_server():
    logger.info("Starting")
    session_server = KomSessionServer(komsession_factory=create_komsession)
    rpcserver = zerorpc.Server(session_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()
