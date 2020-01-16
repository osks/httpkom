import argparse
import asyncio
from functools import partial
import logging
import os
import sys

import cherrypy
from paste.translogger import TransLogger
#import trio
#from hypercorn.trio import serve
from hypercorn.asyncio import serve
from hypercorn.config import Config

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


#class Tracer(trio.abc.Instrument):
#    def before_run(self):
#        print("!!! run started")
#
#    def _print_with_task(self, msg, task):
#        # repr(task) is perhaps more useful than task.name in general,
#        # but in context of a tutorial the extra noise is unhelpful.
#        print("{}: {}".format(msg, task.name))
#
#    def task_spawned(self, task):
#        self._print_with_task("### new task spawned", task)
#
#    def task_scheduled(self, task):
#        self._print_with_task("### task scheduled", task)
#
#    def before_task_step(self, task):
#        self._print_with_task(">>> about to run one step of task", task)
#
#    def after_task_step(self, task):
#        self._print_with_task("<<< task step finished", task)
#
#    def task_exited(self, task):
#        self._print_with_task("### task exited", task)
#
#    def before_io_wait(self, timeout):
#        if timeout:
#            print("### waiting for I/O for up to {} seconds".format(timeout))
#        else:
#            print("### doing a quick check for I/O")
#        self._sleep_time = trio.current_time()
#
#    def after_io_wait(self, timeout):
#        duration = trio.current_time() - self._sleep_time
#        print("### finished I/O check (took {} seconds)".format(duration))
#
#    def after_run(self):
#        print("!!! run finished")


def run_http_server_async(args):
    os.environ['HTTPKOM_SETTINGS'] = args.config
    init_app(app)
    config = Config()
    config.bind = ["{}:{}".format(args.host, args.port)]
    #trio.run(partial(serve, app, config), instruments=[Tracer()])
    asyncio.run(serve(app, config))


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
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

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
    #run_http_server(args)
    run_http_server_async(args)


if __name__ == "__main__":
    main()
