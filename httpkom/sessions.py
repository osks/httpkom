# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

"""
The httpkom connection id is the unique identifier that a httpkom
client uses to identify which LysKOM connection that it owns. Since
httpkom can be configured to allow connections to several different
LysKOM servers, the connection id refers to a specific session on a
specific LysKOM server.

The session number is what the LysKOM server uses to identify an open
connection.

There is a 1-to-1 relation between httpkom connection ids and LysKOM
session numbers. The important difference between the session number
and the connection id, is that the session number is not
secret. Httpkom uses a separate connection identifier, the httpkom
connection id (a random UUID), to make it close to impossible to
intentionally take over another httpkom client's LysKOM connection.

The httpkom connection id is specified as a HTTP header::

  Httpkom-Connection: <uuid>

To open a new connection, make a request like this::

  POST /<server_id>/sessions/
  Content-Type: application/json
  
  { "client": { "name": "jskom", "version": "0.6" } }

The response will look like this::

  HTTP/1.0 201 Created
  Content-Type: application/json
  Httpkom-Connection: <uuid>
  
  { "session_no": 123456 }

This is the only response that will contain the Httpkom-Connection.
The request must not contain any Httpkom-Connnection header. If the
request contains a Httpkom-Connection header, the request will fail
and the response will be::

  HTTP/1.0 409 Conflict

Subsequent request to that server should contain the returned
Httpkom-Connection header. For example, a login request will look
like this::

  POST /<server_id>/sessions/login
  Content-Type: application/json
  Httpkom-Connection: <uuid>
  
  { "pers_no": 14506, "passwd": "test123" }

and the response::

  HTTP/1.0 201 Created
  Content-Type: application/json
  
  { "pers_no": 14506, "pers_name": "Oskars Testperson" }

If a resource requires a logged in session and the request contains a
valid Httpkom-Connection header which is not logged in, the response
will be::

  HTTP/1.0 401 Unauthorized

If the Httpkom-Connection is missing, or if the connection id specified
by the Httpkom-Connection header is invalid (for example if the
connection was to another server than <server_id>, or if there is no
connection with that id), the response will be::

  HTTP/1.0 403 Forbidden

When you get a 403 response, the used Httpkom-Connection should be
considered invalid and should not be used again. If the
Httpkom-Connection specifies a working connection, but to another
server than <server_id>, httpkom might close the connection before
returning 403.

It is up to the client to keep track of opened connection and to use
them with the correct <server_id>. The /<server_id> prefix to all
resources could be seen as redundant, since the Httpkom-Connection
also specifies the server, but it makes the API resources
consistent. Also, the resources on different LysKOM servers has
nothing to do with each other, so it is a good idea from "REST"
perspective to have them different resources (i.e. different
/<server_id> prefixes).

"""

from __future__ import absolute_import
import errno
import functools
import socket
import uuid

from flask import g, request, jsonify

import pylyskom.errors as komerror
from pylyskom.komsession import KomSession, KomPerson, KomSessionNotConnected

from .komserialization import to_dict

from httpkom import HTTPKOM_CONNECTION_HEADER, bp
from .errors import error_response
from .misc import empty_response
from .stats import stats


# These komsessions methods are the only ones that should access the
# _komsessions object

_komsessions = {}

def _open_komsession(host, port, client_name, client_version):
    komsession = KomSession()
    komsession.connect(
        host, port,
        "httpkom", socket.getfqdn(),
        client_name, client_version)
    stats.set('sessions.komsessions.connected.last', 1, agg='sum')
    return komsession

def _save_komsession(ksession):
    connection_id = _new_connection_id()
    assert connection_id not in _komsessions, "Komsession ID already used: {}".format(connection_id)
    _komsessions[connection_id] = ksession
    stats.set('sessions.komsessions.saved.last', 1, agg='sum')
    return connection_id

def _delete_komsession(connection_id):
    if connection_id is None:
        return
    if connection_id in _komsessions:
        del _komsessions[connection_id]
        stats.set('sessions.komsessions.deleted.last', 1, agg='sum')

def _get_komsession(connection_id):
    stats.set('sessions.komsessions.active.last', len(_komsessions), agg='last')
    return _komsessions.get(connection_id, None)

def _new_connection_id():
    return str(uuid.uuid4())




def _get_connection_id_from_request():
    if HTTPKOM_CONNECTION_HEADER in request.headers:
        return request.headers[HTTPKOM_CONNECTION_HEADER]
    else:
        # Work-around for allowing the connection id to be sent as
        # query parameter.  This is needed to be able to show images
        # (text body) by creating an img tag.

        # TODO: This should be considered unsafe, because it would
        # expose the connection id if the user would copy the link.
        return request.args.get(HTTPKOM_CONNECTION_HEADER, None)
    return None


# TODO: Validate that the session pointed out by the
# Httpkom-Connection header is the same as the <server_id>.


def with_connection_id(f):
    """View function decorator. Get the connection id from the request
    and assign it to 'g.connection_id'.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        g.connection_id = _get_connection_id_from_request()
        return f(*args, **kwargs)
    return decorated


def requires_session(f):
    """View function decorator. Check if the request has a
    Httpkom-Connection header that points out a valid LysKOM
    session. If the header is missing, or if there is no session for
    the id, return an empty response with status code 403.
    """
    @functools.wraps(f)
    @with_connection_id
    def decorated(*args, **kwargs):
        g.ksession = _get_komsession(g.connection_id)
        if g.ksession is None:
            return empty_response(403)
        try:
            return f(*args, **kwargs)
        except KomSessionNotConnected:
            _delete_komsession(g.connection_id)
            return empty_response(403)
        except socket.error as e:
            (eno, msg) = e.args
            if eno in (errno.EPIPE, errno.ECONNRESET):
                _delete_komsession(g.connection_id)
                return empty_response(403)
            else:
                raise
    return decorated


def requires_login(f):
    """View function decorator. Check if the request points out a
    logged in LysKOM session. If the session is not logged in, return
    status code 401.
    """
    @functools.wraps(f)
    @requires_session
    def decorated(*args, **kwargs):
        if g.ksession.is_logged_in():
            return f(*args, **kwargs)
        else:
            return empty_response(401)
    return decorated




@bp.route("/sessions/current/who-am-i")
@requires_session
def sessions_who_am_i():
    """TODO
    """
    try:
        session_no = g.ksession.who_am_i()
        if g.ksession.is_logged_in():
            pers_no = g.ksession.get_person_no()
            person = to_dict(KomPerson(pers_no), True, g.ksession)
        else:
            person = None

        return jsonify(dict(person=person, session_no=session_no))
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)


@bp.route("/sessions/current/active", methods=['POST'])
@requires_session
def sessions_current_active():
    """
    Tell the LysKOM server that the current user is active.

    ::

      POST /<server_id>/sessions/current/active HTTP/1.1

    """
    g.ksession.user_is_active()
    return empty_response(204)


@bp.route("/sessions/", methods=['POST'])
@with_connection_id
def sessions_create():
    """Create a new session (a connection to the LysKOM server).
    
    Note: The response body also contains the connection_id (in
    addition to the response header) to around problems with buggy
    CORS implementations[1] in combination with certain javascript
    libraries (AngularJS).
    
    [1] https://bugzilla.mozilla.org/show_bug.cgi?id=608735
    
    .. rubric:: Request
    
    ::
    
      POST /<server_id>/sessions/ HTTP/1.1
      
      {
        "client": { "name": "jskom", "version": "0.2" }
      }
    
    .. rubric:: Responses
    
    Successful connect::
    
      HTTP/1.0 201 Created
      Httpkom-Connection: 033556ee-3e52-423f-9c9a-d85aed7688a1
      
      {
        "session_no": 12345,
        "connection_id": "033556ee-3e52-423f-9c9a-d85aed7688a1"
      }
    
    If the request contains a Httpkom-Connection header::

      HTTP/1.0 409 CONFLICT
    
    """
    if HTTPKOM_CONNECTION_HEADER in request.headers:
        return empty_response(409)
    
    try:
        if request.json is None:
            return error_response(400, error_msg='Invalid body.')

        if 'client' not in request.json:
            return error_response(400, error_msg='Missing "client".')

        client_name = request.json['client']['name']
        client_version = request.json['client']['version']
        
        if g.connection_id is None:
            has_existing_ksession = False
        else:
            has_existing_ksession = True

        # todo: perhaps we should also check if the session is connected?

        if not has_existing_ksession:
            ksession = _open_komsession(
                g.server.host, g.server.port, client_name, client_version)
            connection_id = _save_komsession(ksession)
            response = jsonify(session_no=ksession.who_am_i(), connection_id=connection_id)
            response.headers[HTTPKOM_CONNECTION_HEADER] = connection_id
            return response, 201
        else:
            return empty_response(204)
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)


@bp.route("/sessions/current/login", methods=['POST'])
@requires_session
def sessions_login():
    """Log in using the current session.
    
    Note: If the login is successful, the matched full name will be
    returned in the response.
    
    .. rubric:: Request
    
    ::
    
      POST /<server_id>/sessions/current/login HTTP/1.1
      Httpkom-Connection: <id>
      
      {
        "pers_no": 14506,
        "passwd": "test123"
      }
    
    .. rubric:: Responses
    
    Successful login::
    
      HTTP/1.0 201 Created
      
      {
        "pers_no": 14506,
        "pers_name": "Oskars testperson"
      }
    
    Failed login::
    
      HTTP/1.1 401 Unauthorized
      
    .. rubric:: Example
    
    ::
    
      curl -v -X POST -H "Content-Type: application/json" \\
           -H "Httpkom-Connection: 033556ee-3e52-423f-9c9a-d85aed7688a1" \\
           -d '{ "pers_no": 14506, "passwd": "test123" }' \\
            "http://localhost:5001/lyskom/sessions/current/login"
    
    """
    try:
        pers_no = request.json['pers_no']
        if pers_no is None:
            return error_response(400, error_msg='"pers_no" is null.')
    except KeyError:
        return error_response(400, error_msg='Missing "pers_no".')
    
    try:
        passwd = request.json['passwd']
        if passwd is None:
            return error_response(400, error_msg='"passwd" is null.')
    except KeyError:
        return error_response(400, error_msg='Missing "passwd".')
    
    try:
        kom_person = g.ksession.login(pers_no, passwd)
        return jsonify(to_dict(kom_person, True, g.ksession)), 201
    except (komerror.InvalidPassword, komerror.UndefinedPerson, komerror.LoginDisallowed,
            komerror.ConferenceZero) as ex:
        return error_response(401, kom_error=ex)


@bp.route("/sessions/current/logout", methods=['POST'])
@requires_login
def sessions_logout():
    """Log out in the current session.
    
    .. rubric:: Request
    
    ::
    
      POST /<server_id>/sessions/current/logout HTTP/1.1
      Httpkom-Connection: <id>
      
    .. rubric:: Responses
    
    Successful logout::
    
      HTTP/1.0 204 NO CONTENT
      
    .. rubric:: Example
    
    ::
    
      curl -v -H "Httpkom-Connection: 033556ee-3e52-423f-9c9a-d85aed7688a1" \\
           -X POST "http://localhost:5001/lyskom/sessions/current/logout"
    
    """

    g.ksession.logout()
    return empty_response(204)


@bp.route("/sessions/<int:session_no>", methods=['DELETE'])
@requires_session
def sessions_delete(session_no):
    """Delete a session (disconnect from the LysKOM server).
    
    :param session_no: Session number
    :type session_no: int

    If the request disconnects the current session, the used
    Httpkom-Connection id is no longer valid.
    
    Note (from the protocol A spec): "Session number zero is always
    interpreted as the session making the call, so the easiest way to
    disconnect the current session is to disconnect session zero."
    
    .. rubric:: Request
    
    ::
    
      DELETE /<server_id>/sessions/12345 HTTP/1.1
      Httpkom-Connection: <id>
    
    .. rubric:: Responses
    
    Success::
    
      HTTP/1.1 204 No Content
    
    Session does not exist::
    
      HTTP/1.1 404 Not Found
    
    .. rubric:: Example
    
    ::
    
      curl -v -H "Httpkom-Connection: 033556ee-3e52-423f-9c9a-d85aed7688a1" \\
           -X DELETE "http://localhost:5001/lyskom/sessions/abc123"
    
    """
    try:
        g.ksession.disconnect(session_no)
        # We should delete the connection if we're no longer connected
        # (i.e. we disconnected the curent session).
        if not g.ksession.is_connected():
            _delete_komsession(g.connection_id)
        return empty_response(204)
    except komerror.UndefinedSession as ex:
        return error_response(404, kom_error=ex)


@bp.route("/sessions/current/working-conference", methods=['POST'])
@requires_login
def sessions_change_working_conference():
    """Change current working conference of the current session.
    
    .. rubric:: Request
    
    ::
    
      POST /<server_id>/sessions/current/working-conference HTTP/1.1
      Httpkom-Connection: <id>
      
      {
        "conf_no": 14506,
      }
    
    .. rubric:: Responses
    
    ::
    
      HTTP/1.1 204 No Content
    
    .. rubric:: Example
    
    ::
    
      curl -v -H "Httpkom-Connection: 033556ee-3e52-423f-9c9a-d85aed7688a1" \\
           -X POST -H "Content-Type: application/json" \\
           -d '{ "conf_no": 14506 }' \\
           "http://localhost:5001/lyskom/sessions/current/working-conference"
    
    """
    try:
        conf_no = request.json['conf_no']
        if conf_no is None:
            return error_response(400, error_msg='"conf_no" is null.')
    except KeyError:
        return error_response(400, error_msg='Missing "conf_no".')
    
    g.ksession.change_conference(conf_no)
    return empty_response(204)
