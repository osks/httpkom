# -*- coding: utf-8 -*-

from flask import render_template, request

from flaskapp import app

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
