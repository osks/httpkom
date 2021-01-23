# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from quart import Quart, Blueprint, request, jsonify, g, abort, current_app
import six


# constants
HTTPKOM_CONNECTION_HEADER = 'Httpkom-Connection'

log = logging.getLogger("httpkom")

app = Quart(__name__)
bp = Blueprint('frontend', __name__, url_prefix='/<string:server_id>')


# Patch to fix a bug in Quart.inject_url_defaults.
# (bug reported in https://gitlab.com/pgjones/quart/issues/294)
from itertools import chain
def patched_inject_url_defaults(self, endpoint: str, values: dict) -> None:
    """Injects default URL values into the passed values dict.

    This is used to assist when building urls, see
    :func:`~quart.helpers.url_for`.
    """
    functions = self.url_value_preprocessors[None]
    if '.' in endpoint:
        blueprint = endpoint.rsplit('.', 1)[0]
        functions = chain(functions, self.url_default_functions.get(blueprint, ()))  # type: ignore

    for function in functions:
        function(endpoint, values)

Quart.inject_url_defaults = patched_inject_url_defaults


class default_settings:
    DEBUG = False
    LOG_FILE = None
    LOG_LEVEL = logging.WARNING

    HTTPKOM_LYSKOM_SERVERS = [
        ('lyslyskom', 'LysKOM', 'kom.lysator.liu.se', 4894),
        ]

    HTTPKOM_CROSSDOMAIN_ALLOWED_ORIGINS = '*'
    HTTPKOM_CROSSDOMAIN_MAX_AGE = 0
    HTTPKOM_CROSSDOMAIN_ALLOW_HEADERS = [ 'Origin', 'Accept', 'Content-Type', 'X-Requested-With',
                                          'Cache-Control' ]
    HTTPKOM_CROSSDOMAIN_EXPOSE_HEADERS = [ 'Cache-Control' ]
    HTTPKOM_CROSSDOMAIN_ALLOW_METHODS = [ 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD' ]

    PRESERVE_CONTEXT_ON_EXCEPTION = False


def init_app(app):
    # Use Flask's Config class to read config, as Quart's config
    # handling is not identical to Flask's and it didn't work with our
    # config files.  Flask will parse the config file as it was a
    # Python file, so you can use lists for example. In Quart the list
    # became a string.
    #
    # Hack: Parse with Flask and then convert (via a dict) to Quart.

    import flask
    config = flask.Config(app.config.root_path)

    config.from_object(default_settings)
    if 'HTTPKOM_SETTINGS' in os.environ:
        log.info("Using config file specified by HTTPKOM_SETTINGS environment variable: %s",
                 os.environ['HTTPKOM_SETTINGS'])
        config.from_envvar('HTTPKOM_SETTINGS')
    else:
        log.info("No environment variable HTTPKOM_SETTINGS found, using default settings.")

    config['HTTPKOM_CROSSDOMAIN_ALLOW_HEADERS'].append(HTTPKOM_CONNECTION_HEADER)
    config['HTTPKOM_CROSSDOMAIN_EXPOSE_HEADERS'].append(HTTPKOM_CONNECTION_HEADER)

    # Import config to Quart's app object.
    config_dict = dict(config)
    app.config.from_mapping(config_dict)

    if not app.debug and app.config['LOG_FILE'] is not None:
        # keep 7 days of logs, rotated every midnight
        file_handler = TimedRotatingFileHandler(
            app.config['LOG_FILE'], when='midnight', interval=1, backupCount=7)

        file_handler.setFormatter(logging.Formatter(
               '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
                ))

        file_handler.setLevel(app.config['LOG_LEVEL'])

        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info("Finished setting up file logger.");


    # Load app parts
    from . import conferences
    from . import sessions
    from . import texts
    from . import persons
    from . import memberships
    from . import errors
    from . import server
    from . import stats

    # to avoid pyflakes errors
    dir(conferences)
    dir(sessions)
    dir(texts)
    dir(persons)
    dir(memberships)
    dir(errors)
    dir(server)
    dir(stats)

    app.register_blueprint(bp)


class Server(object):
    def __init__(self, sid, sort_order, name, host, port=4894):
        self.id = sid
        self.sort_order = sort_order
        self.name = name
        self.host = host
        self.port = port

    def to_dict(self):
        return { 'id': self.id, 'sort_order': self.sort_order,
                 'name': self.name, 'host': self.host, 'port': self.port }


# http://flask.pocoo.org/docs/patterns/urlprocessors/
@bp.url_value_preprocessor
def pull_server_id(endpoint, values):
    _servers = dict()
    for i, server in enumerate(current_app.config['HTTPKOM_LYSKOM_SERVERS']):
        _servers[server[0]] = Server(server[0], i, server[1], server[2], server[3])
    server_id = values.pop('server_id')
    if server_id in _servers:
        g.server = _servers[server_id]
    else:
        # No such server
        abort(404)


@app.after_request
def allow_crossdomain(resp):
    def is_allowed(origin):
        allowed_origins = app.config['HTTPKOM_CROSSDOMAIN_ALLOWED_ORIGINS']
        if allowed_origins is not None:
            if isinstance(allowed_origins, six.string_types) and allowed_origins == '*':
                return True
            
            if origin in allowed_origins:
                return True
        
        return False
            
    
    if 'Origin' in request.headers:
        h = resp.headers
        origin = request.headers['Origin']
        if is_allowed(origin):
            h['Access-Control-Allow-Origin'] = origin
                          
            h['Access-Control-Allow-Methods'] = \
                ', '.join(app.config['HTTPKOM_CROSSDOMAIN_ALLOW_METHODS'])
            
            h['Access-Control-Max-Age'] = \
                str(app.config['HTTPKOM_CROSSDOMAIN_MAX_AGE'])
            
            h['Access-Control-Allow-Headers'] = \
                ', '.join(app.config['HTTPKOM_CROSSDOMAIN_ALLOW_HEADERS'])
            
            h['Access-Control-Expose-Headers'] = \
                ', '.join(app.config['HTTPKOM_CROSSDOMAIN_EXPOSE_HEADERS'])
        else:
            h['Access-Control-Allow-Origin'] = 'null'
    
    return resp


@app.after_request
def ios6_cache_fix(resp):
    # Safari in iOS 6 has excessive caching, so this is to stop it
    # from caching our POST requests. We also add Cache-Control:
    # no-cache to any request that doesn't already have a
    # Cache-Control header.
    if request.method == 'POST' or 'Cache-Control' not in resp.headers:
        resp.headers['Cache-Control'] = 'no-cache'
    return resp


@app.route("/")
async def index():
    _servers = dict()
    for i, server in enumerate(current_app.config['HTTPKOM_LYSKOM_SERVERS']):
        _servers[server[0]] = Server(server[0], i, server[1], server[2], server[3])
    servers = dict([ (s.id, s.to_dict()) for s in _servers.values() ])
    return jsonify(servers)
