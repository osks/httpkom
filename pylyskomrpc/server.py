# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging
import uuid

import zerorpc

from pylyskom.errors import ServerError
from pylyskom.cachedconnection import CachingPersonClient
from pylyskom.komsession import KomSessionException

from httpkom.komserialization import to_dict

from .common import EXPOSED_KOMSESSION_METHODS
from .komgevent import GeventConnection, GeventClient, GeventKomSession


logger = logging.getLogger(__name__)


def _new_komsession_id():
    return str(uuid.uuid4())


def create_client(host, port, user):
    def conn_linked(ks):
        logger.debug("GeventConnection is now dead")

    def client_linked(ks):
        logger.debug("GeventClient is now dead")

    conn = GeventConnection(host, port, user)
    conn.link(conn_linked)
    conn.start()

    client = GeventClient(conn)
    client.link(client_linked)
    client.start()

    return CachingPersonClient(client)


def create_komsession():
    ks = GeventKomSession(create_client)
    return ks


class KomSessionServer(object):
    def __init__(self, komsession_factory=create_komsession):
        assert komsession_factory is not None
        self._komsession_factory = komsession_factory
        self._komsessions = dict()

    def create_session(self):
        komsession_id = _new_komsession_id()
        assert not self.has_session(komsession_id)
        self._komsessions[komsession_id] = self._komsession_factory()
        logger.debug("KomSessionServer - has %d komsessions" % (len(self._komsessions),))
        return komsession_id

    def delete_session(self, komsession_id):
        if komsession_id in self._komsessions:
            # make sure the connection is closed before we remove it
            del self._komsessions[komsession_id]
            logger.debug("KomSessionServer has %d komsessions" % (len(self._komsessions),))
            return True
        return False

    def has_session(self, komsession_id):
        return komsession_id in self._komsessions

    def call_session(self, komsession_id, method_name, args, kwargs):
        komsession = self._komsessions[komsession_id]

        if method_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("KomSession has no method called %r" % (method_name,))

        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
    
        # todo: un-dict arguments?

        logger.debug("KomSessionServer - calling KomSession method '%s' with args:%r kwargs:%r"
                        % (method_name, args, kwargs))


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
        except ServerError as ex:
            error_dict = dict(
                type='kom',
                class_name=ex.__class__.__name__,
                args=ex.args)
        except:
            logger.exception("Got unhandled exception in KomSessionServer for method: %s - raising" % method_name)
            raise
        
        logger.debug("KomSessionServer - returning komsession result for method: %s" % method_name)
        return result_dict, error_dict

    @zerorpc.stream
    def stream_session(self, komsession_id):
        komsession = self._komsessions[komsession_id]
        #while True:
        #    msg = komsession.get_async_message()
        #    msg_dict = to_dict(msg, True, komsession)
        #    yield msg_dict

        for msg in komsession._async_queue: # should be ended with StopIteration
            logger.debug("KomSessionServer - streaming komsession msg: %s" % msg)
            msg_dict = to_dict(msg, True, komsession)
            yield msg_dict

        logger.debug("KomSessionServer - done streaming komsession")


    @zerorpc.stream
    def stream(self, komsession_id):
        assert self.has_session(komsession_id)
        komsession = self._komsessions[komsession_id]
        while True:
            msg = komsession._async_queue.get()
            msg_dict = msg.__dict__
            msg_dict['MSG_NO'] = msg.MSG_NO
            yield msg_dict



def run_session_server():
    logger.info("Starting")
    logger.info("Debug logging is on")
    session_server = KomSessionServer(komsession_factory=create_komsession)
    rpcserver = zerorpc.Server(session_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()
