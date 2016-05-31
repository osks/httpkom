# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from flask import g, request, jsonify

import pylyskom.errors as komerror

from .komserialization import to_dict

from httpkom import bp
from .errors import error_response
from .misc import empty_response, get_bool_arg_with_default
from .sessions import requires_session, requires_login


@bp.route('/conferences/')
@requires_session
def conferences_list():
    """Lookup conference names.
    
    Query parameters:
    
    ==========  =======  =================================================================
    Key         Type     Values
    ==========  =======  =================================================================
    name        string   Name to look up according to `KOM conventions <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Name%20Expansion>`_.
    want-pers   boolean  :true: (Default) Include conferences that are mailboxes.
                         :false: Do not include conferences that are mailboxes.
    want-confs  boolean  :true: (Default) Include conferences that are not mailboxes.
                         :false: Do not include conferences that are not mailboxes.
    ==========  =======  =================================================================
        
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/conferences/?name=osk%20t&want-confs=false HTTP/1.0
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.0 200 OK
      
      {
        "conferences": [
          {
            "conf_name": "Oskars tredje person", 
            "conf_no": 13212
          }, 
          {
            "conf_name": "Oskars Testperson", 
            "conf_no": 14506
          }
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET -H "Content-Type: application/json" \\
           "http://localhost:5001/lyskom/conferences/?name=osk%20t&want-confs=false"
    
    """
    name = request.args['name']
    want_pers = get_bool_arg_with_default(request.args, 'want-pers', True)
    want_confs = get_bool_arg_with_default(request.args, 'want-confs', True)
        
    try:
        lookup = g.ksession.lookup_name(name, want_pers, want_confs)
        confs = [ dict(conf_no=t[0], conf_name=t[1]) for t in lookup ]
        return jsonify(dict(conferences=confs))
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)


@bp.route('/conferences/<int:conf_no>')
@requires_login
def conferences_get(conf_no):
    """Get information about a specific conference.
    
    Query parameters:
    
    =======  =======  =================================================================
    Key      Type     Values
    =======  =======  =================================================================
    micro    boolean  :true: (Default) Return micro conference information (`UConference <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Conferences>`_) which causes less load on the server.
                      :false: Return full conference information.
    =======  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/conferences/14506 HTTP/1.1
    
    .. rubric:: Responses
    
    With micro=true::
    
      HTTP/1.0 200 OK
      
      {
        "highest_local_no": 1996, 
        "nice": 77, 
        "type": {
          "forbid_secret": 0, 
          "allow_anonymous": 1, 
          "rd_prot": 1, 
          "secret": 0, 
          "letterbox": 1, 
          "original": 0, 
          "reserved3": 0, 
          "reserved2": 0
        }, 
        "name": "Oskars Testperson", 
        "conf_no": 14506
      }
    
    With micro=false::
    
      HTTP/1.0 200 OK
      
      {
        "super_conf": {
          "conf_name": "", 
          "conf_no": 0
        }, 
        "creator": {
          "pers_no": 14506, 
          "pers_name": "Oskars Testperson"
        }, 
        "no_of_texts": 1977, 
        "no_of_members": 1, 
        "creation_time": "2013-11-30T15:58:06Z",
        "permitted_submitters": {
          "conf_name": "", 
          "conf_no": 0
        }, 
        "conf_no": 14506, 
        "last_written": "2013-11-30T15:58:06Z",
        "keep_commented": 77, 
        "name": "Oskars Testperson", 
        "type": {
          "forbid_secret": 0, 
          "allow_anonymous": 1, 
          "rd_prot": 1, 
          "secret": 0, 
          "letterbox": 1, 
          "original": 0, 
          "reserved3": 0, 
          "reserved2": 0
        }, 
        "first_local_no": 20, 
        "expire": 0, 
        "msg_of_day": 0, 
        "supervisor": {
          "conf_name": "Oskars Testperson", 
          "conf_no": 14506
        }, 
        "presentation": 0, 
        "nice": 77
      }
    
    Conference does not exist::
    
      HTTP/1.0 404 NOT FOUND
      
      { TODO: error stuff }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET "http://localhost:5001/lyskom/conferences/14506?micro=true"
    
    """
    try:
        micro = get_bool_arg_with_default(request.args, 'micro', True)
        return jsonify(to_dict(g.ksession.get_conference(conf_no, micro),
                               True, g.ksession))
    except komerror.UndefinedConference as ex:
        return error_response(404, kom_error=ex)


@bp.route('/conferences/<int:conf_no>/texts/<int:local_text_no>/read-marking', methods=['PUT'])
@requires_login
def conferences_put_text_read_marking(conf_no, local_text_no):
    """Mark text as read in the specified recipient conference (only).
    
    .. rubric:: Request
    
    ::
    
      PUT /<server_id>/conferences/14506/texts/29/read-marking HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 201 Created
    
    .. rubric:: Example
    
    ::
    
      curl -v -X PUT "http://localhost:5001/lyskom/conferences/14506/texts/29/read-marking"
    
    """
    # TODO: handle conferences/texts that doesn't exist (i.e. return 404).
    g.ksession.mark_as_read_local(local_text_no, conf_no)
    return empty_response(201)


@bp.route('/conferences/<int:conf_no>/texts/')
@requires_session
def conferences_get_texts(conf_no):
    """Get the last created texts in the conference. Returns all text
    stats, but not the subject or body.
    
    TODO: Query parameters for pagination.
    
    Query parameters:
    
    ===========  =======  =================================================================
    Key          Type     Values
    ===========  =======  =================================================================
    no-of-texts  integer  Number of text numbers to return. Default: 10
    ===========  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/conferences/texts/ HTTP/1.0
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.0 200 OK
      
      {
        "texts": [
          {
            "recipient_list": [
              {
                "conf_name": "Oskars Testperson",
                "type": "to",
                "loc_no": 29,
                "conf_no": 14506
              }
            ], 
            "author": {
              "pers_no": 14506,
              "pers_name": "Oskars Testperson"
            }, 
            "creation_time": "2013-11-30T15:58:06Z",
            "comment_in_list": [],
            "content_type": "text/x-kom-basic",
            "text_no": 19680717,
            "comment_to_list": [],
          },
          
          ...
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET -H "Content-Type: application/json" \\
           "http://localhost:5001/lyskom/conferences/texts/?no-of-texts=3"
    
    """
    no_of_texts = int(request.args.get('no-of-texts', 10))
    texts = g.ksession.get_last_texts(conf_no, no_of_texts)
    return jsonify(texts=to_dict(texts, True, g.ksession))
