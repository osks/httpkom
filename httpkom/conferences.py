# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from flask import g, request, jsonify

import kom
from komsession import KomSession, KomSessionError, KomText, to_dict, from_dict

from httpkom import app
from errors import error_response
from misc import empty_response, get_bool_arg_with_default
from sessions import requires_session


@app.route('/conferences/')
@requires_session
def conferences_list():
    """Get list of conferences. Which conferences to get are filtered
    with query parameters.
    
    Query parameters:
    
    =======  =======  =================================================================
    Key      Type     Values
    =======  =======  =================================================================
    unread   boolean  :true: Return conferences with unread texts in.
                      :false: *Not implemented.*
    full     boolean  :true: Return full conference information.
                      :false: Return micro conference information (`UConference <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Conferences>`_) which causes less load on the server.
    =======  =======  =================================================================
        
    .. rubric:: Request
    
    ::
    
      GET /conferences/?unread=true HTTP/1.0
    
    .. rubric:: Responses
    
    With full=false::
    
      HTTP/1.0 200 OK
      
      {
        "confs": [
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
        ]
      }
    
    With full=true::
    
      HTTP/1.0 200 OK
      
      {
        "confs": [
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
            "creation_time": "2012-04-28 19:49:11", 
            "permitted_submitters": {
              "conf_name": "", 
              "conf_no": 0
            }, 
            "conf_no": 14506, 
            "last_written": "2012-07-31 00:00:11", 
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
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET -H "Content-Type: application/json" \\
           http://localhost:5001/conferences/?unread=true&full=false
    
    """
    full = get_bool_arg_with_default(request.args, 'full', False)
    unread = get_bool_arg_with_default(request.args, 'unread', False)
    
    if unread:
        return jsonify(confs=to_dict(g.ksession.get_conferences(unread, full),
                                     True, g.ksession))
    else:
        abort(400) # nothing else is implemented


# curl -b cookies.txt -c cookies.txt -v \
#      -X GET http://localhost:5000/conferences/unread/
@app.route('/conferences/unread/')
@requires_session
def conferences_list_unread():
    # this always return confs i "micro format" and has no_of_unread defined, which
    # /conferences/ does not.
    return jsonify(confs=to_dict(g.ksession.get_unread_conferences(),
                                 False, g.ksession))


# curl -b cookies.txt -c cookies.txt -v \
#      -X GET http://localhost:5000/conferences/14506
@app.route('/conferences/<int:conf_no>')
@requires_session
def conferences_get(conf_no):
    try:
        micro = get_bool_arg_with_default(request.args, 'micro', True)
        return jsonify(to_dict(g.ksession.get_conference(conf_no, micro),
                               True, g.ksession))
    except kom.UndefinedConference as ex:
        return error_response(404, kom_error=ex)


# curl -b cookies.txt -c cookies.txt -v \
#      -X GET http://localhost:5000/conferences/14506/read-markings/?unread=true
@app.route('/conferences/<int:conf_no>/read-markings/')
@requires_session
def conferences_get_read_markings(conf_no):
    # Return read-markings. Mostly used with ?unread=true to return
    # unread texts in the given conference.
    # Other functions would be to return 
    
    unread = get_bool_arg_with_default(request.args, 'unread', False)
    
    if unread:
        # TODO: return local_text_no as well
        return jsonify(rms=[ dict(conf_no=conf_no, text_no=text_no, unread=unread)
                             for text_no in g.ksession.\
                                 get_unread_in_conference(conf_no) ])
        
        #return jsonify(text_nos=to_dict(
        #        g.ksession.get_unread_in_conference(conf_no), True, g.ksession))
    else:
        raise NotImplementedError()


# curl -b cookies.txt -c cookies.txt -v \
#      -X PUT http://localhost:5000/conferences/14506/texts/29/read-marking
@app.route('/conferences/<int:conf_no>/texts/<int:local_text_no>/read-marking',
           methods=['PUT'])
@requires_session
def conferences_put_text_read_marking(conf_no, local_text_no):
    # Mark text as read in the specified recipient conference
    
    g.ksession.mark_as_read_local(local_text_no, conf_no)
    return empty_response(204)


# curl -b cookies.txt -c cookies.txt -v \
#      -X DELETE http://localhost:5000/conferences/14506/texts/29/read-marking
@app.route('/conferences/<int:conf_no>/texts/<int:local_text_no>/read-marking',
           methods=['DELETE'])
@requires_session
def conferences_delete_text_read_marking(conf_no, local_text_no):
    # Mark text as unread in the specified recipient conference
    
    raise NotImplementedError()


# TODO: would be nice with GET for read markings as well
