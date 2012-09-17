# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from flask import g, request, jsonify

import kom
from komsession import KomSession, KomSessionError, to_dict

from httpkom import app, bp
from errors import error_response
from misc import empty_response, get_bool_arg_with_default
from sessions import requires_session, requires_login


@bp.route('/persons/', methods=['POST'])
@requires_session
def persons_create():
    """Create a person
    
    .. rubric:: Request
    
    ::
    
      POST /persons/ HTTP/1.0
      
      {
        "name": "Oskars Testperson",
        "passwd": "test123",
      }
    
    .. rubric:: Responses
    
    Person was created::
    
      HTTP/1.0 200 OK
      
      {
        "pers_no": 14506,
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X POST H "Content-Type: application/json" \\
           -d '{ "name": "Oskar Testperson", "passwd": "test123" }' \\
           http://localhost:5001/persons/
    
    """
    if g.ksession:
        # Use exising session if we have one
        ksession = g.ksession
    else:
        # .. otherwise create a new temporary session
        ksession = KomSession(app.config['HTTPKOM_LYSKOM_SERVER'])
        ksession.connect()
    
    name = request.json['name']
    passwd = request.json['passwd']
    
    try:
        #lookup = ksession.lookup_name(name, want_pers, want_confs)
        #confs = [ dict(conf_no=t[0], conf_name=t[1]) for t in lookup ]
        pers_no = ksession.create_person(name, passwd)
        return jsonify(dict(pers_no=pers_no))
    except kom.Error as ex:
        return error_response(400, kom_error=ex)
    finally:
        # if we created a new session, close it
        if not g.ksession:
            ksession.disconnect()


# Or should the URL be /persons/current/memberships/<int:conf_no>/no-of-unread ?
@bp.route('/persons/current/memberships/<int:conf_no>', methods=['POST'])
@requires_login
def persons_set_unread(conf_no):
    """Set number of unread texts in current persons membership for
    the given conference.
    
    .. rubric:: Request
    
    ::
    
      POST /persons/current/memberships/14506 HTTP/1.1
      
      {
        "no_of_unread": 17
      }
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 204 OK
    
    .. rubric:: Example
    
    ::
    
      curl -v -X POST -H "Content-Type: application/json" \\
           -d { "no_of_unread": 17 } \\
           http://localhost:5001/persons/current/memberships/14506
    
    """
    # The property in the JSON object body is just a wrapper because
    # most (all?) JSON libraries doesn't handle just sending a number
    # in the body; they expect/require an object or an array.
    try:
        no_of_unread = request.json['no_of_unread']
    except KeyError as ex:
        return error_response(400, error_msg='Missing "no_of_unread".')
    
    g.ksession.set_unread(conf_no, no_of_unread)
    return empty_response(204)


@bp.route('/persons/<int:pers_no>/memberships/<int:conf_no>')
@requires_login
def persons_get_membership(pers_no, conf_no):
    """Get a persons membership for a conference.
    
    Query parameters:
    
    ===========  =======  =================================================================
    Key          Type     Values
    ===========  =======  =================================================================
    want-unread  boolean  :true: Include unread text numbers.
                          :false: (Default) Do not include unread text numbers.
    ===========  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /persons/14506/memberships/14506 HTTP/1.0
    
    .. rubric:: Responses
    
    With want-unread=false::
    
      HTTP/1.0 200 OK
      
      {
        "conference": {
          "conf_name": "Oskars Testperson", 
          "conf_no": 14506
        }, 
        "priority": 255, 
        "added_at": "2012-04-28 19:49:11", 
        "position": 3, 
        "type": {
          "passive": 0, 
          "secret": 0, 
          "passive_message_invert": 0, 
          "invitation": 0
        }, 
        "last_time_read": "2012-08-19 17:14:46", 
        "added_by": {
          "pers_no": 14506, 
          "pers_name": "Oskars Testperson"
        },
        "no_of_unread": 2,
        "unread_texts": null
      }
    
    With want-unread=true::
    
      HTTP/1.0 200 OK
      
      {
        "conference": {
          "conf_name": "Oskars Testperson", 
          "conf_no": 14506
        }, 
        "priority": 255, 
        "added_at": "2012-04-28 19:49:11", 
        "position": 3, 
        "type": {
          "passive": 0, 
          "secret": 0, 
          "passive_message_invert": 0, 
          "invitation": 0
        }, 
        "last_time_read": "2012-08-19 17:14:46", 
        "added_by": {
          "pers_no": 14506, 
          "pers_name": "Oskars Testperson"
        },
        "no_of_unread": 2,
        "unread_texts": [
          19831603,
          19831620
        ]
      }
    
    Not a member::
    
      HTTP/1.0 404 NOT FOUND
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET http://localhost:5001/persons/14506/memberships/14506?want-unread=false
    
    """
    want_unread = get_bool_arg_with_default(request.args, 'want-unread', False)
    
    try:
        return jsonify(to_dict(g.ksession.get_membership(pers_no, conf_no, want_unread),
                               True, g.ksession))
    except kom.NotMember as ex:
        return error_response(404, kom_error=ex)


@bp.route('/persons/<int:pers_no>/memberships/<int:conf_no>', methods=['PUT'])
@requires_login
def persons_put_membership(pers_no, conf_no):
    """Add the person as member to the given conference, or update an
    existing membership.
    
    Query parameters:
    
    ===========  =======  =================================================================
    Key          Type     Values
    ===========  =======  =================================================================
    priority     int      (Default 100) The priority of the membership.
    where        int      (Default 0) The position in the membership list.
    ===========  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      PUT /persons/14506/memberships/6 HTTP/1.1
    
    .. rubric:: Response
    
    Success::
    
      HTTP/1.1 204 OK
    
    If the person or conference do not exist::
    
      HTTP/1.1 404 NOT FOUND
    
    .. rubric:: Example
    
    ::
    
      curl -v -X PUT http://localhost:5001/persons/14506/memberships/6?priority=150
    
    """
    priority = int(request.args.get('priority', 100))
    where = int(request.args.get('where', 0))
    try:
        g.ksession.add_membership(pers_no, conf_no, priority, where)
        return empty_response(204)
    except (kom.UndefinedPerson, kom.UndefinedConference) as ex:
        return error_response(404, kom_error=ex)


@bp.route('/persons/<int:pers_no>/memberships/<int:conf_no>', methods=['DELETE'])
@requires_login
def persons_delete_membership(pers_no, conf_no):
    """Remove the persons membership in the given conference.
    
    .. rubric:: Request
    
    ::
    
      DELETE /persons/14506/memberships/6 HTTP/1.1
    
    .. rubric:: Response
    
    Success::
    
      HTTP/1.1 204 OK
    
    If the person or conference do not exist, or if the membership do
    not exist::
    
      HTTP/1.1 404 NOT FOUND
    
    .. rubric:: Example
    
    ::
    
      curl -v -X DELETE http://localhost:5001/persons/14506/memberships/6
    
    """
    try:
        g.ksession.delete_membership(pers_no, conf_no)
        return empty_response(204)
    except (kom.UndefinedPerson, kom.UndefinedConference, kom.NotMember) as ex:
        return error_response(404, kom_error=ex)


@bp.route('/persons/<int:pers_no>/memberships/')
@requires_login
def persons_list_memberships(pers_no):
    """Get list of memberships.
    
    Query parameters:
    
    ===========  =======  =================================================================
    Key          Type     Values
    ===========  =======  =================================================================
    unread       boolean  :true: Only return memberships with unread texts in.
                          :false: (Default) (Not implemented) Return all memberships.
    want-unread  boolean  :true: Include unread text numbers.
                          :false: (Default) Do not include unread text numbers.
    ===========  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /persons/14506/memberships/ HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 200 OK
      
      {
        "memberships": [
          {
            "conference": {
              "conf_name": "Oskars Testperson", 
              "conf_no": 14506
            }, 
            "priority": 255, 
            "added_at": "2012-04-28 19:49:11", 
            "position": 3, 
            "type": {
              "passive": 0, 
              "secret": 0, 
              "passive_message_invert": 0, 
              "invitation": 0
            }, 
            "last_time_read": "2012-08-19 17:14:46", 
            "added_by": {
              "pers_no": 14506, 
              "pers_name": "Oskars Testperson"
            },
            "no_of_unread": 2,
            "unread_texts": [
              19831603,
              19831620
            ]
          },
          
          ...
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET http://localhost:5001/persons/14506/memberships/?unread=true
    
    """
    unread = get_bool_arg_with_default(request.args, 'unread', False)
    want_unread = get_bool_arg_with_default(request.args, 'want-unread', False)
    memberships = g.ksession.get_memberships(pers_no, unread, want_unread)
    return jsonify(memberships=to_dict(memberships, True, g.ksession))
