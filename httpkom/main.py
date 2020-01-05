import argparse
import logging
import os
import sys

import cherrypy
from paste.translogger import TransLogger

from pylyskom import stats
from pylyskom.stats import stats as pylyskom_stats
from httpkom.stats import stats as httpkom_stats
from httpkom import app, init_app


log = logging.getLogger("httpkom.main")


def start_stats_sender(graphite_host, graphite_port):
    if graphite_host and graphite_port:
        log.info("Sending stats to Graphite at {}:{}".format(graphite_host, graphite_port))
        conn = stats.GraphiteTcpConnection(graphite_host, graphite_port)
        sender = stats.StatsSender([ pylyskom_stats, httpkom_stats ], conn, interval=10)
        sender.start()
    else:
        log.info("No Graphite host and port specified, not sending stats")


def run_http_server(args):
    os.environ['HTTPKOM_SETTINGS'] = args.config
    init_app(app)

    # Enable WSGI access logging via Paste
    app_logged = TransLogger(app)

    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app_logged, '/')

    # Set the configuration of the web server
    cherrypy.config.update({
        'engine.autoreload_on': True,
        'log.screen': True,
        'server.socket_port': args.port,
        'server.socket_host': args.host,
        'server.thread_pool': 1,
        'server.thread_pool_max': 1,
    })
    cherrypy.log.access_log.propagate = False
    cherrypy.log.error_log.propagate = False

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--config', help='Path to configuration file',
                        required=True)

    parser.add_argument('--host', help='Hostname or IP to listen on',
                        default='0.0.0.0')
    parser.add_argument('--port', help='Port to listen on',
                        type=int, default=5001)

    parser.add_argument('--graphite-host', help='Hostname or IP to Graphite server to send stats to',
                        default=None)
    parser.add_argument('--graphite-port', help='Port for Graphite plaintext protocol',
                        type=int, default=2003)

    args = parser.parse_args()

    log.info("Using args: %s", args)

    args.config = os.path.abspath(args.config)
    if not os.path.exists(args.config):
        log.info("Config file does not exist: %s", args.config)
        sys.exit(1)

    start_stats_sender(args.graphite_host, args.graphite_port)
    run_http_server(args)


if __name__ == "__main__":
    main()
