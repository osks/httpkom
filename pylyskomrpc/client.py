# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import functools

import zerorpc

from pylyskom import kom
from pylyskom.komsession import KomSession
from httpkom import app # todo: stop using

from common import EXPOSED_KOMSESSION_METHODS


class KomSessionProxy(object):
    def __init__(self, remote_komsession_client, komsession_id):
        self._remote_komsession_client = remote_komsession_client
        self._komsession_id = komsession_id

    def __getattr__(self, attr_name):
        if attr_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("Session has no method called %r" % (attr_name,))
        def proxy_method(*args, **kwargs):
            return self._remote_komsession_client.call_session(
                self._komsession_id, attr_name, args, kwargs)
        return proxy_method


class RemoteKomSessionClient(object):
    def __init__(self, rpc_client):
        self._rpc_client = rpc_client

    def create_session(self, host, port):
        app.logger.debug("create_session(%s, %s)" % (host, port))
        return self._rpc_client.create_session(host, port)

    def delete_session(self, komsession_id):
        app.logger.debug("delete_session(%s)" % (komsession_id,))
        return self._rpc_client.delete_session(komsession_id)

    def has_session(self, komsession_id):
        app.logger.debug("has_session(%s)" % (komsession_id,))
        has_session = self._rpc_client.has_session(komsession_id)
        return has_session

    def get_session(self, komsession_id):
        app.logger.debug("get_session(%s)" % (komsession_id,))
        return KomSessionProxy(self, komsession_id)

    def call_session(self, komsession_id, method_name, args, kwargs):
        # todo: dicitify arguments
        
        app.logger.debug("call_session(%s) '%s' with args:%r kwargs:%r"
                        % (komsession_id, method_name, args, kwargs))
    
        # zerorpc does not support keyword arguments, so send the
        # args array and kwargs dict as normal arguments
        try:
            result, error = self._rpc_client.call_session(
                komsession_id, method_name, args, kwargs)
    
            if error is not None:
                app.logger.debug("Got remote remote error: %s" % (error,))
                if error['type'] == 'komsession':
                    raise getattr(komsession, error['class_name'])(*error['args'])
                elif error['type'] == 'kom':
                    raise getattr(kom, error['class_name'])(*error['args'])
                else:
                    raise Exception("Got unknown remote error")
        except zerorpc.RemoteError as rex:
            print "RemoteError: name=%s  msg=%s" % (rex.name, rex.msg)
            raise rex
        
        # todo: un-dict the result?

        return result


def create_client():
    # todo: set timeout that matches other configuration (such as gunicorn, etc)
    rpc_client = zerorpc.Client(timeout=30, heartbeat=2)
    rpc_client.connect('tcp://127.0.0.1:12345')
    return RemoteKomSessionClient(rpc_client)
