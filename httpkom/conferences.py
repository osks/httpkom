# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from flask import g, request, jsonify

import kom
from komsession import KomSession, KomSessionError, KomText, to_dict, from_dict

from httpkom import app
from errors import error_response
from misc import empty_response, get_bool_arg_with_default
from sessions import requires_session, optional_session


@app.route('/conferences/')
@optional_session
def conferences_list():
    """Lookup conference names.
    
    An existing session is not required, but if one exist (i.e. valid
    cookie) it will be used. Otherwise a new session will be created
    temporarily for this request.
    
    Query parameters:
    
    ==========  =======  =================================================================
    Key        Type     Values
    ==========  =======  =================================================================
    name        string   Name to look up according to `KOM conventions <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Name%20Expansion>`_.
    want_pers   boolean  :true: (Default) Include conferences that are mailboxes.
                         :false: Do not include conferences that are mailboxes.
    want_confs  boolean  :true: (Default) Include conferences that are not mailboxes.
                         :false: Do not include conferences that are not mailboxes.
    ==========  =======  =================================================================
        
    .. rubric:: Request
    
    ::
    
      GET /conferences/?name=osk%20t&want_confs=false HTTP/1.0
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.0 200 OK
      
      {
        "confs": [
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
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET -H "Content-Type: application/json" \\
           http://localhost:5001/conferences/?name=osk%20t&want_confs=false
    
    """
    name = request.args['name']
    want_pers = get_bool_arg_with_default(request.args, 'want_pers', True)
    want_confs = get_bool_arg_with_default(request.args, 'want_confs', True)
    if g.ksession:
        # Use exising session if we have one
        ksession = g.ksession
    else:
        # .. otherwise create a new temporary session
        ksession = KomSession(app.config['HTTPKOM_LYSKOM_SERVER'])
        ksession.connect()
        
    try:
        lookup = ksession.lookup_name(name, want_pers, want_confs)
        confs = [ dict(conf_no=t[0], conf_name=t[1]) for t in lookup ]
        return jsonify(dict(confs=confs))
    except kom.Error as ex:
        return error_response(400, kom_error=ex)
    finally:
        # if we created a new session, close it
        if not g.ksession:
            ksession.disconnect()


@app.route('/conferences/unread/')
@requires_session
def conferences_list_unread():
    """Get list of unread conferences with information about how many
    unread texts each conference has.
    
    .. rubric:: Request
    
    ::
    
      GET /conferences/unread/ HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 200 OK
      
      {
        "confs": [
          {
            "no_of_unread": 265, 
            "name": "Oskars Testperson", 
            "conf_no": 14506
          }
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET http://localhost:5001/conferences/unread/
    
    """
    return jsonify(confs=to_dict(g.ksession.get_unread_conferences(),
                                 False, g.ksession))


@app.route('/conferences/<int:conf_no>')
@requires_session
def conferences_get(conf_no):
    """Get information about a specific conference.
    
    =======  =======  =================================================================
    Key      Type     Values
    =======  =======  =================================================================
    micro    boolean  :true: (Default) Return micro conference information (`UConference <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Conferences>`_) which causes less load on the server.
                      :false: Return full conference information.
    =======  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /conferences/14506 HTTP/1.1
    
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
    
    Conference does not exist::
    
      HTTP/1.0 404 NOT FOUND
      
      { TODO: error stuff }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET http://localhost:5001/conferences/14506?micro=true
    
    """
    try:
        micro = get_bool_arg_with_default(request.args, 'micro', True)
        return jsonify(to_dict(g.ksession.get_conference(conf_no, micro),
                               True, g.ksession))
    except kom.UndefinedConference as ex:
        return error_response(404, kom_error=ex)


@app.route('/conferences/<int:conf_no>/no-of-unread', methods=['POST'])
@requires_session
def conferences_set_unread(conf_no):
    """ Expecting:
            Content-Type: application/json 
            Body: { "no_of_unread": 123 }}
        Example:
            curl -b cookies.txt -c cookies.txt -v -X POST -H "Content-Type: application/json" \
                http://localhost:5001/conferences/14506/no-of-unread -d '{ "no_of_unread": 10 }'
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


        
@app.route('/conferences/<int:conf_no>/read-markings/')
@requires_session
def conferences_get_read_markings(conf_no):
    """Return read-markings. Mostly used with *unread=true* to return
    unread texts in the given conference.
    
    .. rubric:: Request
    
    ::
    
      GET /conferences/14506/read-markings/?unread=true HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 200 OK
      
      {
        "rms": [
          {
            "text_no": 19791715, 
            "unread": true, 
            "conf_no": 14506
          }, 
          {
            "text_no": 19791718, 
            "unread": true, 
            "conf_no": 14506
          }
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET http://localhost:5001/conferences/14506/read-markings/?unread=true
    
    """
    unread = get_bool_arg_with_default(request.args, 'unread', False)
    
    if unread:
        # TODO: return local_text_no as well
        return jsonify(rms=[ dict(conf_no=conf_no, text_no=text_no, unread=unread)
                             for text_no in g.ksession.\
                                 get_unread_in_conference(conf_no) ])
    else:
        raise NotImplementedError()


@app.route('/conferences/<int:conf_no>/texts/<int:local_text_no>/read-marking', methods=['PUT'])
@requires_session
def conferences_put_text_read_marking(conf_no, local_text_no):
    """Mark text as read in the specified recipient conference (only).
    
    .. rubric:: Request
    
    ::
    
      PUT /conferences/14506/texts/29/read-marking HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 204 OK
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X PUT http://localhost:5001/conferences/14506/texts/29/read-marking
    
    """
    # TODO: handle conferences/texts that doesn't exist (i.e. return 404).
    g.ksession.mark_as_read_local(local_text_no, conf_no)
    return empty_response(204)


@app.route('/conferences/<int:conf_no>/texts/<int:local_text_no>/read-marking',
           methods=['DELETE'])
@requires_session
def conferences_delete_text_read_marking(conf_no, local_text_no):
    """(*Not implemented*) Mark text as unread in the specified recipient conference (only).
    
    .. rubric:: Request
    
    ::
    
      DELETE /conferences/14506/texts/29/read-marking HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 204 OK
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X DELETE http://localhost:5001/conferences/14506/texts/29/read-marking
    
    """
    raise NotImplementedError()


# TODO: would it be nice with GET for a read markings as well (for a specific text)?
