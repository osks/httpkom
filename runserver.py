#!/usr/bin/env python
# -*- coding: utf-8 -*-

from httpkom import app


def main():
    # use 127.0.0.1 instead of localhost to avoid delays related to ipv6.
    # http://werkzeug.pocoo.org/docs/serving/#troubleshooting
    app.run(host='127.0.0.1', port=5001, debug=True)


if __name__ == "__main__":
    main()
