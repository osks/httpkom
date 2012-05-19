# -*- coding: utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, render_template, request

app = Flask(__name__)



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


crossdomain_allowed_origins = [ 'https://jskom.osd.se', 'http://localhost:5000' ]
crossdomain_allow_headers = [ 'Origin', 'Accept', 'Cookie', 'Content-Type',
                              'X-Requested-With' ]
crossdomain_expose_headers = [ 'Set-Cookie', 'Cookie' ]
crossdomain_max_age = 1 #21600
crossdomain_allow_methods = [ 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS' ]


@app.after_request
def allow_crossdomain(resp):
    if 'Origin' in request.headers:
        h = resp.headers
        origin = request.headers['Origin']
        if (origin in crossdomain_allowed_origins
            or '*' in crossdomain_allowed_origins):
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = ', '.join(crossdomain_allow_methods)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Max-Age'] = str(crossdomain_max_age)
            h['Access-Control-Allow-Headers'] = ', '.join(crossdomain_allow_headers)
            h['Access-Control-Expose-Headers'] = ', '.join(crossdomain_expose_headers)
        else:
            h['Access-Control-Allow-Origin'] = 'null'
    
    return resp


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/status")
def status():
    return render_template('status.html', kom_sessions=sessions.kom_sessions)
