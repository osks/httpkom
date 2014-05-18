# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import zerorpc

from pylyskom import komsession, kom
from httpkom import app


class SessionProxy(object):
    def __init__(self, remote_kom_client, komsession_id):
        self._remote_kom_client = remote_kom_client
        self._komsession_id = komsession_id

    def __getattr__(self, attr_name):
        def proxy_method(*args, **kwargs):
            return self._remote_kom_client.call_komsession(
                self._komsession_id, attr_name, *args, **kwargs)
        return proxy_method


class RemoteKomClient(object):
    def __init__(self, rpc_client):
        self._rpc_client = rpc_client

    def create_session(self, host, port):
        return self._rpc_client.create_session(host, port)

    def delete_session(self, komsession_id):
        return self._rpc_client.delete_session(komsession_id)

    def has_session(self, komsession_id):
        return self._rpc_client.has_session(komsession_id)

    def get_session(self, komsession_id):
        komsession_proxy = SessionProxy(self, komsession_id)
        return komsession_proxy

    def call_komsession(self, komsession_id, method_name, *args, **kwargs):
        # todo: serialize arguments
        
        app.logger.debug("Calling remote method '%s' with args:%r kwargs:%r"
                        % (method_name, args, kwargs))

        # zerorpc does not support keyword arguments, so send the
        # args array and kwargs dict as normal arguments
        try:
            result, error = self._rpc_client.call_komsession_method(
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
        
        # todo: deserialize result
        return result


def get_client():
    rpc_client = zerorpc.Client()
    rpc_client.connect('tcp://127.0.0.1:12345')
    return RemoteKomClient(rpc_client)
