# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import json
import functools

from flask import request, render_template, g
from zerorpc import TimeoutExpired
from gevent import Greenlet
#from geventwebsocket import WebSocketError

from pylyskomrpc.client import create_client

from httpkom import app
from sessions import with_connection_id, get_connection_id_from_request
from errors import error_response
from misc import empty_response

from flask.ext.websockets import websocket


class KomAsyncWebsocket(Greenlet):
    def __init__(self, websocket, komsession_id, client, komsession):
        Greenlet.__init__(self)
        self._websocket = websocket
        self._komsession_id = komsession_id
        self._client = client
        self._komsession = komsession

    def _run(self):
        print "KomAsyncWebsocket - starting loop for id: %s" % self._komsession_id
        while True:
            #message = websocket.receive()
            #websocket.send(message)

            #async_messages = self._komsession.get_async_messages()
            #for msg in async_messages:
            #    msg_dict = dict(async_msg=str(msg))
            #    self._websocket.send(json.dumps(msg_dict))
            #gevent.sleep(1)

            try:
                print "KomAsyncWebsocket - streaming for id: %s" % self._komsession_id
                #for msg in self._client.stream_session(self._komsession_id):
                for msg in self._komsession.stream_async_messages():
                    print "KomAsyncWebsocket - sending: %s" % msg
                    self._websocket.send(json.dumps(msg))
            except TimeoutExpired:
                print "KomAsyncWebsocket - timed out"

        print "KomAsyncWebsocket - ending loop for id: %s" % self._komsession_id


@app.route('/async')
#@with_connection_id
#@requires_session
def websocket_open():
    print "websocket - open"
    if websocket is None:
        return error_response(500, "WebSocket initialization failed")

    komsession_id = get_connection_id_from_request(request)

    client = create_client()
    if not client.has_session(komsession_id):
        print "websocket - no komsession found for id: %s" % komsession_id
        websocket.close()
        return empty_response(400) # this shouldn't be needed

    def close(komwebsocket):
        websocket.close()
        client.close()
        return

    #komsession = g.ksession
    komsession = client.get_session(komsession_id)
    print "websocket - opening websocket with komsession_id: %s" % komsession_id
    handler = KomAsyncWebsocket(websocket, komsession_id, client, komsession)
    handler.link(close)
    handler.start()
    handler.join()
    print "websocket - end."
    return empty_response(204) # this shouldn't be neede


@app.route('/websocket')
@with_connection_id
def websocket_index():
    #komsession_id = g.connection_id

    client = create_client()
    ks_id = client.create_session()
    ks = client.get_session(ks_id)
    host = "localhost"
    #host = "kom.lysator.liu.se"
    ks.connect(host, 4894,
               "oskar", "localhost",
               "test", "0.1")
    person_no = ks.lookup_name_exact("oskars testperson", want_pers=True, want_confs=False)
    ks.login(person_no, "oxide24")
    komsession_id = ks_id

    print "oskar: komsession_id: %s" % komsession_id
    return render_template('websocket.html', komsession_id=komsession_id)
