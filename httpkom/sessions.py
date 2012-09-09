# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import uuid
import json
import functools

from flask import g, abort, request, jsonify, make_response, Response

import kom
from komsession import KomSession, KomSessionError, AmbiguousName, NameNotFound, to_dict

from httpkom import app
from errors import error_response
from misc import empty_response
import version


_kom_server = app.config['HTTPKOM_LYSKOM_SERVER']

_cookie_domain = app.config['HTTPKOM_COOKIE_DOMAIN']
_cookie_name = 'connection_id'

_komsessions = {}


# Terminology:

# connection_id - The UUID for our KomSession. The ID is stored in the
#                 cookie and is considered secret! (You can take over
#                 some ones session with it.)

# session - an open connection to the LysKOM server. WhoAmI will
#           return your session number. Does not need to be logged in.


# TODO: To better handle multiple sessions, we should use headers for
# session handling. With that I mean that we should supply all
# information needed for opening a new session in the headers
# (basically just client name/version).


def requires_login(f):
    """Check if the request has a LysKOM session (i.e. a cookie
    specifying a valid connection) and that it's logged in. If there
    is no session, returns 428 (see requires_session). If the session is not 
    logged in, returns status code 401.
    
    Note: The status code 428 ("Precondition Required") comes from RFC 6585.
    http://tools.ietf.org/html/rfc6585
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        g.ksession = _get_komsession(_get_connection_id())
        # TODO: can we wrap "us" with requires_session instead of
        # implementing the same behavior?
        if g.ksession:
            if g.ksession.is_logged_in():
                return f(*args, **kwargs)
            else:
                return empty_response(401)
        else:
            return empty_response(428)
    return decorated

def requires_session(f):
    """Check if the request has a LysKOM session (i.e. a cookie
    specifying a valid connection). If there is no session, returns an
    empty response with status code 428.
    
    Note: The status code 428 ("Precondition Required") comes from RFC 6585.
    http://tools.ietf.org/html/rfc6585
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        g.ksession = _get_komsession(_get_connection_id())
        if g.ksession:
            return f(*args, **kwargs)
        else:
            return empty_response(428)
    return decorated


# TODO: if we complete the rewrite to only have create/delete sessions
# for opening/closing lyskom sessions (connections), we don't really
# need all of these helper methods.

def _new_connection_id():
    return str(uuid.uuid4())

def _save_komsession(ksession):
    connection_id = _new_connection_id()
    _komsessions[connection_id] = ksession
    return connection_id

def _delete_connection():
    connection_id = request.cookies.get(_cookie_name)
    if connection_id is not None and connection_id in _komsessions:
        del _komsessions[connection_id]

def _get_connection_id():
    if _cookie_name in request.cookies:
        return request.cookies.get(_cookie_name)
    return None

def _get_komsession(connection_id):
    if connection_id is not None and connection_id in _komsessions:
        return _komsessions[connection_id]
    return None


@app.route("/sessions/current/who-am-i")
@requires_session
def sessions_who_am_i():
    """
    """
    try:
        return jsonify(to_dict(g.ksession, True, g.ksession))
    except kom.Error as ex:
        return error_response(400, kom_error=ex)


@app.route("/sessions/", methods=['POST'])
def sessions_create():
    """Create a new session (a connection to the LysKOM server).
    
    .. rubric:: Request
    
    ::
    
      POST /sessions/ HTTP/1.1
      
      {
        "client": { "name": "jskom", "version": "0.2" }
      }
    
    .. rubric:: Responses
    
    Successful connect::
    
      HTTP/1.0 200 OK
      Set-Cookie: connection_id=033556ee-3e52-423f-9c9a-d85aed7688a1; expires=Sat, 19-May-2012 12:44:51 GMT; Max-Age=604800; Path=/
      
      { "session_no": 12345 }
    
    Already connected::

      HTTP/1.0 204 NO CONTENT
    
    """
    try:
        client_name = request.json['client']['name']
        client_version = request.json['client']['version']
        
        existing_ksession = _get_komsession(_get_connection_id())
        if existing_ksession is None:
            ksession = KomSession(_kom_server)
            ksession.connect(client_name, client_version)
            response = jsonify(session_no=ksession.who_am_i())
            connection_id = _save_komsession(ksession)
            response.set_cookie(_cookie_name, domain=_cookie_domain,
                                value=connection_id, max_age=7*24*60*60)
            return response
        else:
            return empty_response(204)
    except kom.Error as ex:
        return error_response(400, kom_error=ex)


@app.route("/sessions/current/login", methods=['POST'])
@requires_session
def sessions_login():
    """Log in with a session.
    
    Note: If the login is successful, the matched full name will be
    returned in the response.
    
    .. rubric:: Request
    
    ::
    
      POST /sessions/ HTTP/1.1
      
      {
        "person": { "pers_no": 14506, "passwd": "test123" }
      }
    
    .. rubric:: Responses
    
    Successful login::
    
      HTTP/1.0 200 OK
      
      {
        "session_no": 12345,
        "person": { "pers_no": 14506, "pers_name": "Oskars testperson" }
      }
    
    Failed login::
    
      HTTP/1.1 401 Unauthorized
      
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X POST -H "Content-Type: application/json" \\
           -d '{ "person": { "pers_no": 14506, "passwd": "test123" } }' \\
            http://localhost:5001/sessions/
    
    """
    try:
        person = request.json['person']
        if person is None:
            return error_response(400, error_msg='"person" is null.')
    except KeyError as ex:
        return error_response(400, error_msg='Missing "person".')
    
    try:
        pers_no = person['pers_no']
        if pers_no is None:
            return error_response(400, error_msg='"pers_no" in "person" is null.')
    except KeyError as ex:
        return error_response(400, error_msg='Missing "pers_no" in "person".')
    
    try:
        passwd = person['passwd']
        if passwd is None:
            return error_response(400, error_msg='"passwd" in "person" is null.')
    except KeyError as ex:
        return error_response(400, error_msg='Missing "passwd" in "person".')
    
    try:
        g.ksession.login(pers_no, passwd)
        return jsonify(to_dict(g.ksession, True, g.ksession))
    except (kom.InvalidPassword, kom.UndefinedPerson, kom.LoginDisallowed,
            kom.ConferenceZero) as ex:
        return error_response(401, kom_error=ex)
    except kom.Error as ex:
        return error_response(400, kom_error=ex)


@app.route("/sessions/current/logout", methods=['POST'])
@requires_login
def sessions_logout():
    """Logout in the current session.
    """
    try:
        g.ksession.logout()
        return empty_response(204)
    except kom.Error as ex:
        return error_response(400, kom_error=ex)


@app.route("/sessions/<int:session_no>", methods=['DELETE'])
@requires_login
def sessions_delete(session_no):
    """Delete a session (disconnect from the LysKOM server).
    
    Note (from the protocol A spec): "Session number zero is always
    interpreted as the session making the call, so the easiest way to
    disconnect the current session is to disconnect session zero."
    
    .. rubric:: Request
    
    ::
    
      DELETE /sessions/12345 HTTP/1.1
    
    .. rubric:: Responses
    
    We disconnected out our own session::
    
      HTTP/1.1 204 No Content
      Set-Cookie: connection_id=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Path=/

    We disconnected another session::
    
      HTTP/1.1 204 No Content
    
    Session does not exist::
    
      HTTP/1.1 404 Not Found
      Set-Cookie: session_no=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Path=/
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X DELETE http://localhost:5001/sessions/abc123
    
    """
    try:
        g.ksession.disconnect(session_no)
        response = empty_response(204)
        if not g.ksession.is_connected():
            _delete_connection()
            response.set_cookie(_cookie_name, value='', expires=0)
        return response
    except kom.UndefinedSession as ex:
        return error_response(404, kom_error=ex)
    except kom.Error as ex:
        return error_response(400, kom_error=ex)


@app.route("/sessions/current/working-conference", methods=['POST'])
@requires_session
def sessions_change_working_conference():
    """Change current working conference of the current session.
    
    .. rubric:: Request
    
    ::
    
      POST /sessions/current/working-conference HTTP/1.1
      
      {
        "conf_no": 14506,
      }
    
    .. rubric:: Responses
    
    ::
    
      HTTP/1.1 204 No Content
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X POST -H "Content-Type: application/json" \\
           -d '{ "conf_no": 14506 }' \\
           http://localhost:5001/sessions/current/working-conference
    
    """
    try:
        conf_no = request.json['conf_no']
        if conf_no is None:
            return error_response(400, error_msg='"conf_no" is null.')
    except KeyError as ex:
        return error_response(400, error_msg='Missing "conf_no".')
    
    try:
        g.ksession.change_conference(conf_no)
        return empty_response(204)
    except kom.Error as ex:
        return error_response(400, kom_error=ex)
