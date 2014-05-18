# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import errno
import logging
import socket

import gevent
import zerorpc

from pylyskom import kom
from pylyskom.komsession import KomSession, KomSessionException

from komsessionstorage import KomSessionStorage
from komserialization import to_dict


logger = logging.getLogger(__name__)


class RemoteKomServer(object):
    def __init__(self, storage):
        self._storage = storage

    def create_session(self, host, port):
        return self._storage.new(host, port)

    def delete_session(self, komsession_id):
        if self._storage.has(komsession_id):
            # make sure we have close the connection
            self._storage.get(komsession_id).close()
        return self._storage.remove(komsession_id)

    def has_session(self, komsession_id):
        return self._storage.has(komsession_id)

    def call_komsession_method(self, komsession_id, attr_name, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()

        logger.debug("Got remote call to '%s' with args:%r kwargs:%r"
                     % (attr_name, args, kwargs))
        
        # todo: deserialize arguments

        komsession = self._storage.get(komsession_id)
        
        result_dict = None
        error_dict = None
        try:
            result = getattr(komsession, attr_name)(*args, **kwargs)
            result_dict = to_dict(result, True, komsession)
        except socket.error as (eno, msg):
            if eno in (errno.EPIPE, errno.ECONNRESET):
                # disconnected
                # todo return some error so that the client knows it should send 403.
                self._storage.remove(komsession_id)
            raise
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
    pass


def setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    #root_logger = logging.getLogger()
    #root_logger.addHandler(ch)

    zerorpc_logger = logging.getLogger('zerorpc')
    zerorpc_logger.addHandler(ch)


def test():
    while True:
        print "hej"
        gevent.sleep(1)


def run_storage_server():
    #gevent.spawn(test)

    storage = KomSessionStorage(komsession_factory=GeventKomSession)
    storage_server = RemoteKomServer(storage)

    rpcserver = zerorpc.Server(storage_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()


if __name__ == "__main__":
    setup_logging()
    run_storage_server()
