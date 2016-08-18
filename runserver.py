#!/usr/bin/env python
# -*- coding: utf-8 -*-

from httpkom import app


def main():
    from pylyskom import stats
    from pylyskom.stats import stats as pylyskom_stats
    from httpkom.stats import stats as httpkom_stats
    conn = stats.GraphiteTcpConnection('127.0.0.1', 2003)
    sender = stats.StatsSender([ pylyskom_stats, httpkom_stats ], conn, interval=10)
    sender.start()

    # use 127.0.0.1 instead of localhost to avoid delays related to ipv6.
    # http://werkzeug.pocoo.org/docs/serving/#troubleshooting

    # TODO: make it work with threaded=True
    app.run(host='127.0.0.1', port=5001, debug=True)


if __name__ == "__main__":
    main()
