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
    
      POST /<server_id>/persons/ HTTP/1.0
      
      {
        "name": "Oskars Testperson",
        "passwd": "test123",
      }
    
    .. rubric:: Responses
    
    Person was created::
    
      HTTP/1.0 201 Created
      
      {
        "pers_no": 14506,
        "pers_name": "Oskars Testperson"
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X POST H "Content-Type: application/json" \\
           -d '{ "name": "Oskar Testperson", "passwd": "test123" }' \\
           http://localhost:5001/lyskom/persons/
    
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
        kom_person = ksession.create_person(name, passwd)
        return jsonify(to_dict(kom_person, True, g.ksession)), 201
    except kom.Error as ex:
        return error_response(400, kom_error=ex)
    finally:
        # if we created a new session, close it
        if not g.ksession:
            ksession.disconnect()
