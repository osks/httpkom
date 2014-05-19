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


def _call_komsession_method(komsession, method_name, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = dict()

    # todo: deserialize arguments?

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
            # make sure we have closed the connection
            self._storage.get(komsession_id).close()
        return self._storage.remove(komsession_id)

    def has_session(self, komsession_id):
        return self._storage.has(komsession_id)


def _wrap_komsession_method(method_name):
    def wrapper(self, komsession_id, args, kwargs):
        logger.debug("Got remote call to '%s' with args:%r kwargs:%r"
                     % (method_name, args, kwargs))
    
        komsession = self._storage.get(komsession_id)
        return _call_komsession_method(komsession, method_name, args, kwargs)
    wrapped = getattr(KomSession, method_name)
    functools.update_wrapper(wrapper, wrapped)
    return wrapper

def _add_komsession_methods(method_names, cls):
    for method_name in method_names:
        logger.debug("Registering method '%s' on %s" % (method_name, cls.__name__))
        # NOTE: we prefix methods with "ks_" because some of them
        # collide with zerorpc (such as 'connect').
        setattr(cls, 'ks_' + method_name, _wrap_komsession_method(method_name))





#class GeventKomSession(KomSession):
#    pass


#def test():
#    while True:
#        print "hej"
#        gevent.sleep(1)


#gevent.spawn(test)


def run_session_server():
    _add_komsession_methods(EXPOSED_KOMSESSION_METHODS, KomSessionServer)

    logger.info("Starting")
    session_server = KomSessionServer()
    rpcserver = zerorpc.Server(session_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()
