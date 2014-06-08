# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oskar Skoog. Released under GPL.

import logging
import socket

import gevent
import gevent.socket
from gevent import Greenlet
from gevent.event import Event, AsyncResult
from gevent.queue import Queue, Empty

from pylyskom.async import AsyncMessages
from pylyskom.cachedconnection import Client
from pylyskom.connection import Connection
from pylyskom.errors import ReceiveError
from pylyskom.komsession import KomSession


logger = logging.getLogger(__name__)


class GeventKomSession(KomSession):
    def connect(self, host, port, username, hostname, client_name, client_version):
        KomSession.connect(self, host, port, username, hostname, client_name, client_version)
        self._async_queue = Queue()
        self.subscribe_async()

    def subscribe_async(self):
        self._client.register_async_handler(AsyncMessages.NEW_TEXT, self._handle_async)
        self._client.register_async_handler(AsyncMessages.LOGIN, self._handle_async)
        self._client.register_async_handler(AsyncMessages.LOGOUT, self._handle_async)

    def get_async_messages(self, limit=100):
        messages = []
        try:
            for _ in xrange(limit):
                messages.append(self._async_queue.get_nowait())
        except Empty:
            pass
        return messages

    def get_async_message(self):
        return self._async_queue.get()

    def _handle_async(self, msg):
        #gevent.sleep(30) # for testing
        logger.info("GeventKomSession - got async message: %s" % (msg,))
        self._async_queue.put(msg)


class GeventClient(Greenlet):
    def __init__(self, conn):
        Greenlet.__init__(self)
        self._conn = conn
        self._client = None
        self._ok_queue = {}
        self._error_queue = {}
        self._request_queue = Queue()
        self._async_handler_func = None
        self._close_event = Event()
    
    def close(self):
        self._close_event.set()

    def set_async_handler(self, handler_func):
        self._async_handler_func = handler_func

    def request(self, request):
        ar = AsyncResult()
        logger.debug("GeventClient - sending request: %s" % (request,))
        ref_no = self._conn.send_request(request)
        self._request_queue.put((ref_no, ar))
        return ar.get()

    def _run(self):
        logger.debug("GeventClient - starting")
        self._client = Client(self._conn)
        while True:
            if self._close_event.is_set():
                break
            ref_no, async_result = self._request_queue.get()
            self._wait_and_dequeue(ref_no, async_result)
        
        self._conn.close()
        logger.debug("GeventClient - done.")

    def _wait_and_dequeue(self, ref_no, async_result):
        """Wait for a request to be answered, return response or raise
        error.
        """
        logger.debug("GeventClient - waiting for  response ref_no: %s" % (ref_no,))
        while ref_no not in self._ok_queue and \
              ref_no not in self._error_queue:
            if self._close_event.is_set():
                return

            self._read_response()

        if ref_no in self._ok_queue:
            resp = self._ok_queue[ref_no]
            logger.debug("GeventClient - got response %s ref_no: %s" % (resp, ref_no))
            del self._ok_queue[ref_no]
            async_result.set(resp)
        elif ref_no in self._error_queue:
            error = self._error_queue[ref_no]
            logger.debug("GeventClient - got error %s ref_no: %s" % (error, ref_no))
            del self._error_queue[ref_no]
            async_result.set_exception(error)
        else:
            raise RuntimeError("Got unknown ref-no: %r" % (ref_no,))

    def _read_response(self):
        ref_no, resp, error = self._conn.read_response()
        logger.debug("GeventClient - read response for ref_no: %s" % (ref_no,))
        if ref_no is None:
            # async message
            self._handle_async_message(resp)
        elif error is not None:
            # error reply
            self._error_queue[ref_no] = error
        else:
            # ok reply - resp can be None
            self._ok_queue[ref_no] = resp

    def _handle_async_message(self, msg):
        if self._async_handler_func is not None:
            # TODO: is this really safe?
            logger.debug("GeventClient - handling async message: %s" % (msg,))
            gevent.spawn(self._async_handler_func, msg)



class GeventConnection(Greenlet):
    def __init__(self, host, port, user):
        Greenlet.__init__(self)
        self._send_queue = Queue()
        self._read_queue = Queue()
        self._close_event = Event()

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

    def _connect(self):
        logger.debug("GeventConnection - connecting")
        self._sock = gevent.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port))
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
                ref_no = self._conn.send_request(req)
                logger.debug("GeventConnection - sent request %s with ref_no: %s" % (req, ref_no))
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
            #logger.debug("GeventConnection - reading response")
            try:
                ref_no, resp, error = self._conn.read_response()
            except ReceiveError:
                # this seem to be expected after close() now. could we
                # make it nicer so we don't need to expect to get an exception?
                logger.info("Failed to read, got ReceiveError. Closing connection.")
                self.close()
                break

            logger.debug("GeventConnection - read ref_no: %s, response: %s" % (ref_no, resp))
            self._read_queue.put((ref_no, resp, error))
        
        logger.debug("GeventConnection - ending read loop")
