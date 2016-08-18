# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from flask import g, request, jsonify

import pylyskom.errors as komerror

from .komserialization import to_dict

from httpkom import bp
from .errors import error_response
from .sessions import requires_session, requires_login
from .misc import empty_response


@bp.route('/persons/<int:pers_no>/user-area/<string:block_name>', methods=['GET'])
@requires_login
def persons_get_user_area_block(pers_no, block_name):
    """Get a user area block
    """
    block = g.ksession.get_user_area_block(pers_no, block_name)
    print(block)
    if block is None:
        return empty_response(404)
    return jsonify(block)


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
    name = request.json['name']
    passwd = request.json['passwd']
    
    try:
        kom_person = g.ksession.create_person(name, passwd)
        return jsonify(to_dict(kom_person, True, g.ksession)), 201
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)
