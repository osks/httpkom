# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging

import zerorpc

from pylyskom import kom, komsession

from httpkom import app # todo: stop using

from common import EXPOSED_KOMSESSION_METHODS


logger = logging.getLogger(__name__)


class KomSessionProxy(object):
    def __init__(self, remote_kom_client, komsession_id):
        self._remote_kom_client = remote_kom_client
        self._komsession_id = komsession_id

    def __getattr__(self, attr_name):
        if attr_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("KomSession has no method called %r" % (attr_name,))
        def proxy_method(*args, **kwargs):
            return self._remote_kom_client.call_komsession(
                self._komsession_id, attr_name, *args, **kwargs)
        return proxy_method

    def stream_async_messages(self):
        for r in self._remote_komsession_client._rpc_client.stream_session(self._komsession_id):
            yield r


class RemoteKomSessionClient(object):
    def __init__(self, rpc_client):
        self._rpc_client = rpc_client

    def create_session(self, host, port):
        return self._rpc_client.create_session(host, port)

    def delete_session(self, komsession_id):
        logger.debug("delete_session(%s)" % (komsession_id,))
        assert komsession_id is not None
        return self._rpc_client.delete_session(komsession_id)

    def has_session(self, komsession_id):
        logger.debug("has_session(%s)" % (komsession_id,))
        assert komsession_id is not None
        has_session = self._rpc_client.has_session(komsession_id)
        return has_session

    def get_session(self, komsession_id):
        logger.debug("get_session(%s)" % (komsession_id,))
        assert komsession_id is not None
        assert self._rpc_client.has_session(komsession_id)
        return KomSessionProxy(self, komsession_id)

    def call_session(self, komsession_id, method_name, args, kwargs):

        # todo: dicitify arguments?
        
        logger.debug("call_session(%s) '%s' with args:%r kwargs:%r"
                        % (komsession_id, method_name, args, kwargs))

        assert komsession_id is not None
        assert self._rpc_client.has_session(komsession_id)
    
        # zerorpc does not support keyword arguments, so send the
        # args array and kwargs dict as normal arguments
        try:
            # NOTE: we prefix methods with "ks_" because some of them
            # collide with zerorpc (such as 'connect').
            result, error = getattr(self._rpc_client, 'ks_' + method_name)(
                komsession_id, args, kwargs)

            if error is not None:
                logger.debug("Got remote remote error: %s" % (error,))
                if error['type'] == 'komsession':
                    raise getattr(komsession, error['class_name'])(*error['args'])
                elif error['type'] == 'kom':
                    raise getattr(komerror, error['class_name'])(*error['args'])
                else:
                    raise Exception("Got unknown remote error")
        except zerorpc.RemoteError as rex:
            print "RemoteError: name=%s  msg=%s" % (rex.name, rex.msg)
            raise rex
        
        # todo: deserialize result
        return result


def _wrap_komsession_method(attr_name):
    def wrapper(self, komsession_id, *args, **kwargs):
        return self.call_komsession(komsession_id, attr_name, *args, **kwargs)
    #wrapped = getattr(KomSession, attr_name)
    #functools.update_wrapper(wrapper, wrapped)
    return wrapper


def _add_komsession_methods(method_names, cls):
    for method_name in method_names:
        setattr(cls, method_name, _wrap_komsession_method(method_name))


def create_client():
    _add_komsession_methods(EXPOSED_KOMSESSION_METHODS, RemoteKomSessionClient)

    rpc_client = zerorpc.Client()
    rpc_client.connect('tcp://127.0.0.1:12345')
    return RemoteKomSessionClient(rpc_client)
