#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gevent.wsgi import WSGIServer

from httpkom import app


def setup_logging():
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    zerorpc_logger = logging.getLogger('zerorpc')
    zerorpc_logger.addHandler(ch)

def main():
    setup_logging()
    # use 127.0.0.1 instead of localhost to avoid delays related to ipv6.
    # http://werkzeug.pocoo.org/docs/serving/#troubleshooting
    #app.run(host='127.0.0.1', port=5001, debug=True)
    http_server = WSGIServer(('127.0.0.1', 5001), app)
    http_server.serve_forever()

if __name__ == "__main__":
    main()
