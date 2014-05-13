# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import logging
import uuid

import zerorpc

from pylyskom.komsession import KomSession

from komserialization import to_dict


logger = logging.getLogger(__name__)


def _new_komsession_id():
    return str(uuid.uuid4())


class InMemoryKomSessionStorage(object):
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
    

class KomSessionStorageClient(object):
    def __init__(self, rpc_client):
        self._rpc_client = rpc_client

    def new(self, host, port):
        return self._rpc_client.new(host, port)
    
    def remove(self, komsession_id):
        return self._rpc_client.remove(komsession_id)
    
    def has(self, komsession_id):
        return self._rpc_client.has(komsession_id)

    def get(self, komsession_id):
        if not self._rpc_client.has(komsession_id):
            raise KeyError(repr(komsession_id))
        return KomSessionRemoteProxy(self._rpc_client, komsession_id)


class KomSessionRemoteProxy(object):
    def __init__(self, rpc_client, komsession_id):
        assert rpc_client is not None
        assert komsession_id is not None
        self._rpc_client = rpc_client
        self._komsession_id = komsession_id

    def __getattr__(self, attr_name):
        def method(*args, **kwargs):
            # todo: serialize arguments
            
            logger.info("Calling remote method '%s' with args:%r kwargs:%r"
                        % (attr_name, args, kwargs))

            # zerorpc does not support keyword arguments, so send the
            # args array and kwargs dict as normal arguments
            result = self._rpc_client.call_komsession(
                self._komsession_id, attr_name, args, kwargs)
            
            # todo: deserialize result
            return result
        return method


class KomSessionStorageServer(object):
    def __init__(self, storage):
        self._storage = storage

    def new(self, host, port):
        return self._storage.new(host, port)
    
    def remove(self, komsession_id):
        return self._storage.remove(komsession_id)
    
    def has(self, komsession_id):
        return self._storage.has(komsession_id)

    def get(self, komsession_id):
        # TODO: What should we return? Raise? Proxy-function?
        #return self._storage.get(komsession_id)
        raise Exception("Cannot get from a storage server")

    def call_komsession(self, komsession_id, attr_name, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()

        logger.info("Got remote call to '%s' with args:%r kwargs:%r"
                    % (attr_name, args, kwargs))

        # todo: deserialize arguments

        komsession = self._storage.get(komsession_id)
        result = getattr(komsession, attr_name)(*args, **kwargs)
        result_dict = to_dict(result, True, komsession)
        return result_dict


def get_storage_client():
    rpc_client = zerorpc.Client()
    rpc_client.connect('tcp://127.0.0.1:12345')
    return KomSessionStorageClient(rpc_client)
