# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging
import uuid
import socket

import gevent
import gevent.socket
from gevent import Greenlet
from gevent.event import Event, AsyncResult
from gevent.queue import Queue

import zerorpc

from pylyskom.async import AsyncMessages, async_dict
from pylyskom.errors import ServerError, ReceiveError, UnimplementedAsync
from pylyskom.connection import Connection
from pylyskom.cachedconnection import Client, CachingPersonClient
from pylyskom.komsession import KomSession, KomSessionException

from httpkom.komserialization import to_dict

from common import EXPOSED_KOMSESSION_METHODS


logger = logging.getLogger(__name__)


def _new_komsession_id():
    return str(uuid.uuid4())


class GeventKomSession(KomSession):
    def connect(self, host, port, username, hostname, client_name, client_version):
        KomSession.connect(self, host, port, username, hostname, client_name, client_version)
        self.register_async_handler()
        self.async_queue = Queue()

    def register_async_handler(self):
        self._conn.register_async_handler(AsyncMessages.NEW_TEXT, self._handle_async)
        self._conn.register_async_handler(AsyncMessages.LOGIN, self._handle_async)
        self._conn.register_async_handler(AsyncMessages.LOGOUT, self._handle_async)
        
    def _handle_async(self, msg):
        #gevent.sleep(30) # for testing
        logger.info("GeventKomSession - got async message: %s" % (msg,))
        self.async_queue.put(msg)


class GeventConnection(Greenlet):
    def __init__(self, host, port, user):
        Greenlet.__init__(self)
        self._send_queue = Queue()
        self._read_queue = Queue()
        self._close_event = Event()
        self._async_handlers = {}

        self._sock = None
        self._conn = None

        self._host = host
        self._port = port
        self._user = user

    def send_request(self, req):
        async_ref_no = AsyncResult()
        self._send_queue.put((async_ref_no, req))
        return async_ref_no.get()

    def read_response(self):
        return self._read_queue.get()

    def close(self):
        self._close_event.set()

    def register_async_handler(self, msg_no, handler):
        """Register a handler for a type of async message.

        @param msg_no Type of async message.

        @param handler Function that should be called when an async
        message of the specified type is received.
        """
        if msg_no not in async_dict:
            raise UnimplementedAsync
        if msg_no in self._async_handlers:
            self._async_handlers[msg_no].append(handler)
        else:
            self._async_handlers[msg_no] = [handler]

    def _handle_async_message(self, msg):
        if msg.MSG_NO in self._async_handlers:
            for handler in self._async_handlers[msg.MSG_NO]:
                # spawning handler
                gevent.spawn(handler, msg)

    def _connect(self):
        logger.debug("GeventConnection - connecting")
        self._sock = gevent.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port)) # todo: move to run?
        self._conn = Connection(self._sock, self._user)

    def _disconnect(self):
        logger.debug("GeventConnection - shutting down")
        self._conn.close()
        self._conn = None
        self._sock = None

    def _run(self):
        logger.debug("GeventConnection - starting")
        self._connect()
        sl = gevent.spawn(self._send_loop)
        rl = gevent.spawn(self._read_loop)
        self._close_event.wait()
        sl.kill()
        rl.kill()
        sl.join()
        rl.join()
        self._disconnect()
        logger.debug("GeventConnection - done.")

    def _send_loop(self):
        logger.debug("GeventConnection - starting send loop")
        while True:
            logger.debug("GeventConnection - send loop")
            async_ref_no, req = self._send_queue.get()
            # do we need wait_write or not?
            #gevent.socket.wait_write(self._sock.fileno())
            try:
                logger.debug("GeventConnection - sending request: %s" % (req,))
                ref_no = self._conn.send_request(req)
                logger.debug("GeventConnection - sent request with ref_no: %s" % (ref_no,))
                async_ref_no.set(ref_no)
            except Exception as e:
                logger.exception("Failed to send request")
                async_ref_no.set_exception(e)
            #gevent.sleep(0)

        logger.debug("GeventConnection - ending send loop")
        

    def _read_loop(self):
        logger.debug("GeventConnection - starting read loop")
        while True:
            #gevent.sleep(0)
            logger.debug("GeventConnection - read loop")

            # why doesn't it work with wait_read?
            #gevent.socket.wait_read(self._sock.fileno())
            logger.debug("GeventConnection - reading response")
            try:
                ref_no, resp, error = self._conn.read_response()
            except ReceiveError:
                # this seem to be expected after close() now. could we
                # make it nicer so we don't need to expect to get an exception?
                logger.info("Failed to read, got ReceiveError. Closing connection.")
                self.close()
                break

            if ref_no is None:
                logger.debug("GeventConnection - got async message %s" % (resp,))
                self._handle_async_message(resp)
            else:
                logger.debug("GeventConnection - got request response for %s" % (ref_no,))
                self._read_queue.put((ref_no, resp, error))
        
        logger.debug("GeventConnection - ending read loop")



def create_client(host, port, user):
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.connect((host, port))
    #conn = Connection(sock, user)
    def linked(ks):
        logger.debug("GeventConnection is now dead")

    conn = GeventConnection(host, port, user)
    conn.link(linked)
    conn.start()
    client = Client(conn)
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
        logger.debug("KomSessionServer has %d komsessions" % (len(self._komsessions),))
        return komsession_id

    def delete_session(self, komsession_id):
        assert komsession_id is not None
        if komsession_id in self._komsessions:
            # make sure the connection is closed before we remove it
            del self._komsessions[komsession_id]
            logger.debug("KomSessionServer has %d komsessions" % (len(self._komsessions),))
            return True
        return False

    def has_session(self, komsession_id):
        assert komsession_id is not None
        return komsession_id in self._komsessions

    def call_session(self, komsession_id, method_name, args, kwargs):
        assert self.has_session(komsession_id)
        komsession = self._komsessions[komsession_id]

        if method_name not in EXPOSED_KOMSESSION_METHODS:
            raise AttributeError("KomSession has no method called %r" % (method_name,))

        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
    
        # todo: un-dict arguments?

        logger.debug("calling KomSession instance")

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
    
        logger.debug("returning komsession result")
        return result_dict, error_dict

    @zerorpc.stream
    def stream(self, komsession_id):
        assert self.has_session(komsession_id)
        komsession = self._komsessions[komsession_id]
        while True:
            msg = komsession.async_queue.get()
            msg_dict = msg.__dict__
            msg_dict['MSG_NO'] = msg.MSG_NO
            yield msg_dict


    @zerorpc.stream
    def streaming_range(self, fr, to, step):
        return xrange(fr, to, step)



def run_session_server():
    logger.info("Starting")
    logger.info("Debug logging is on")
    session_server = KomSessionServer(komsession_factory=create_komsession)
    rpcserver = zerorpc.Server(session_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()
