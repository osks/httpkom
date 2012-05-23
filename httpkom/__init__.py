# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, render_template, request

from misc import empty_response


class default_settings:
    DEBUG = False
    HTTPKOM_COOKIE_DOMAIN = None
    
    HTTPKOM_CROSSDOMAIN_ALLOWED_ORIGINS = '*'
    HTTPKOM_CROSSDOMAIN_MAX_AGE = 0
    HTTPKOM_CROSSDOMAIN_ALLOW_HEADERS = [ 'Origin', 'Accept', 'Cookie', 'Content-Type',
                                          'X-Requested-With' ]
    HTTPKOM_CROSSDOMAIN_EXPOSE_HEADERS = [ 'Set-Cookie', 'Cookie' ]
    HTTPKOM_CROSSDOMAIN_ALLOW_METHODS = [ 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD' ]
    HTTPKOM_CROSSDOMAIN_ALLOW_CREDENTIALS = 'true'


app = Flask(__name__)
app.config.from_object(default_settings)
if 'HTTPKOM_SETTINGS' in os.environ:
    app.config.from_envvar('HTTPKOM_SETTINGS')
else:
    app.logger.info("No environment variable HTTPKOM_SETTINGS found, using default settings.")


#if not app.debug:
#    #file_handler = logging.FileHandler("httpkom.log")
#    
#    # keep 7 days of logs, rotated every midnight
#    file_handler = TimedRotatingFileHandler(
#        "log.txt", when='midnight', interval=1, backupCount=7)
#    
#    file_handler.setFormatter(logging.Formatter(
#           '%(asctime)s %(levelname)s: %(message)s '
#            '[in %(pathname)s:%(lineno)d]'
#            ))
#    
#    #file_handler.setLevel(logging.WARNING)
#    file_handler.setLevel(logging.DEBUG)
#    
#    app.logger.addHandler(file_handler)
#    app.logger.setLevel(logging.DEBUG)
#    app.logger.info("hej");



# Load app parts
import conferences
import sessions
import texts



@app.after_request
def allow_crossdomain(resp):
    def is_allowed(origin):
        allowed_origins = app.config['HTTPKOM_CROSSDOMAIN_ALLOWED_ORIGINS']
        if allowed_origins is not None:
            if isinstance(allowed_origins, basestring) and allowed_origins == '*':
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
            
            h['Access-Control-Allow-Credentials'] = \
                app.config['HTTPKOM_CROSSDOMAIN_ALLOW_CREDENTIALS']
            
            h['Access-Control-Max-Age'] = \
                str(app.config['HTTPKOM_CROSSDOMAIN_MAX_AGE'])
            
            h['Access-Control-Allow-Headers'] = \
                ', '.join(app.config['HTTPKOM_CROSSDOMAIN_ALLOW_HEADERS'])
            
            h['Access-Control-Expose-Headers'] = \
                ', '.join(app.config['HTTPKOM_CROSSDOMAIN_EXPOSE_HEADERS'])
        else:
            h['Access-Control-Allow-Origin'] = 'null'
    
    return resp


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/status")
def status():
    # Only enable status page in debug mode. It's not public information!
    # IMPORTANT: the kom_session.id is VERY secret! You can take over a session with it.
    if app.config['DEBUG']:
        return render_template('status.html', kom_sessions=sessions.kom_sessions)
    else:
        return empty_response(404)
