import argparse
import asyncio
import logging
import os
import sys

from hypercorn.asyncio import serve
from hypercorn.config import Config

from pylyskom import stats
from pylyskom.stats import stats as pylyskom_stats
from httpkom.stats import stats as httpkom_stats
from httpkom import app, init_app
from httpkom.sessions import keepalive_loop


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
    config = Config()
    config.bind = ["{}:{}".format(args.host, args.port)]

    async def run():
        if args.keepalive_interval > 0:
            asyncio.create_task(keepalive_loop(args.keepalive_interval, args.keepalive_timeout))
        await serve(app, config)

    asyncio.run(run())


def main():
    parser = argparse.ArgumentParser(description='Httpkom')

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

    parser.add_argument('--keepalive-interval', type=float, default=0,
                        help='Seconds between keepalive requests on each LysKOM connection (0: off)')

    parser.add_argument('--keepalive-timeout', type=float, default=30,
                        help='Seconds to wait for a keepalive reply before closing the connection')

    parser.add_argument('--log-level', help='Log level (DEBUG logs all LysKOM protocol traffic)',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)-7s %(name)-15s %(message)s',
                        level=getattr(logging, args.log_level))

    log.info("Using args: %s", args)

    args.config = os.path.abspath(args.config)
    if not os.path.exists(args.config):
        log.info("Config file does not exist: %s", args.config)
        sys.exit(1)

    start_stats_sender(args.graphite_host, args.graphite_port)
    run_http_server(args)


if __name__ == "__main__":
    main()
