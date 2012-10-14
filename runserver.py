#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent.pywsgi import WSGIServer
from gevent import monkey; monkey.patch_all()

from httpkom import app


if __name__ == "__main__":
    address = 'localhost', 5001
    http_server = WSGIServer(address, app)
    try:
        print "Server running on port %s:%d. Ctrl+C to quit" % address
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.stop()
        print "Stopped."
