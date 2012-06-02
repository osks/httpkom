# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import io
import StringIO

from flask import g, request, jsonify, send_file, Response

import kom
from komsession import KomSession, KomSessionError, KomText, to_dict, from_dict, \
    parse_content_type, mime_type_tuple_to_str

from httpkom import app
from errors import error_response
from misc import empty_response
from sessions import requires_session


@app.route('/texts/<int:text_no>')
@requires_session
def texts_get(text_no):
    """Get a text.
    
    Note: The body will only be included in the response if the content type is text.
    
    .. rubric:: Request
    
    ::
    
      GET /texts/19680717 HTTP/1.0
    
    .. rubric:: Responses
    
    Text exists::
    
      HTTP/1.0 200 OK
      
      {
        "body": "r\u00e4ksm\u00f6rg\u00e5s",
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
        "creation_time": "2012-05-08 18:36:17",
        "comment_in_list": [],
        "content_type": "text/x-kom-basic",
        "text_no": 19680717,
        "comment_to_list": [],
        "subject": "jaha"
      }
    
    Text does not exist::
    
      HTTP/1.0 404 NOT FOUND
      
      { TODO: error stuff }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET -H "Content-Type: application/json" \\
           http://localhost:5001/texts/19680717
    
    """
    try:
        return jsonify(to_dict(g.ksession.get_text(text_no), True, g.ksession))
    except kom.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@app.route('/texts/<int:text_no>/body')
@requires_session
def texts_get_body(text_no):
    """Get the body of text, with the content type of the body set in the HTTP header.
    Useful for creating img-tags in HTML and specifying this URL as source.
    
    If the content type is text, the text will be recoded to UTF-8. For other types,
    the content type will be left untouched.
    
    .. rubric:: Request
    
    ::
    
      GET /texts/19680717/body HTTP/1.0
    
    .. rubric:: Responses
    
    Text exists::
    
      HTTP/1.0 200 OK
      Content-Type: text/x-kom-basic; charset=utf-8
      
      räksmörgås
    
    Text does not exist::
    
      HTTP/1.0 404 NOT FOUND
      
      { TODO: error stuff }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET -H "Content-Type: application/json" \\
           http://localhost:5001/texts/19680717/body
    
    """
    try:
        text = g.ksession.get_text(text_no)
        mime_type, encoding = parse_content_type(text.content_type)
        
        #data = io.BytesIO()
        data = StringIO.String()
        if mime_type[0] == 'text':
            data.write(text.body.encode('utf-8'))
        else:
            data.write(text.body)
        data.flush()
        data.seek(0)
        response = send_file(data,
                             mimetype=text.content_type,
                             as_attachment=False)
            
        return response
    except kom.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@app.route('/texts/', methods=['POST'])
@requires_session
def texts_create():
    """Create a text.
    
    .. rubric:: Request
    
    ::
    
      POST /texts/ HTTP/1.0
      
      {
        "body": "r\u00e4ksm\u00f6rg\u00e5s",
        "subject": "jaha",
        "recipient_list": [ { "conf_name": "oska testp", "type": "to" } ],
        "content_type": "text/x-kom-basic",
        "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ]
      }
    
    .. rubric:: Responses
    
    Text was created::
    
      HTTP/1.0 200 OK
      
      {
        "text_no": 19724960, 
      }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X POST H "Content-Type: application/json" \\
           -d '{ "body": "r\u00e4ksm\u00f6rg\u00e5s", \\
                 "subject": "jaha",
                 "recpipent_list": [ { "conf_name": "oska testp", "type": "to" } ], \\
                 "content_type": "text/x-kom-basic", \\
                 "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ] }' \\
           http://localhost:5001/texts/
    
    """
    komtext = from_dict(request.json, KomText, True, g.ksession)
    text_no = g.ksession.create_text(komtext)
    return jsonify(text_no=text_no)


@app.route('/texts/<int:text_no>/read-marking', methods=['PUT'])
@requires_session
def texts_put_read_marking(text_no):
    """Mark a text as read in all recipient conferences.
    
    .. rubric:: Request
    
    ::
    
      PUT /texts/<int:text_no>/read-marking HTTP/1.0
    
    .. rubric:: Responses
    
    Text was marked as read::
    
      HTTP/1.0 204 NO CONTENT
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X PUT http://localhost:5001/texts/19680717/read-marking
    
    """
    g.ksession.mark_as_read(text_no)
    return empty_response(204)


# curl -b cookies.txt -c cookies.txt -v \
#      -X DELETE http://localhost:5000/texts/19680717/read-marking
@app.route('/texts/<int:text_no>/read-marking', methods=['DELETE'])
@requires_session
def texts_delete_read_marking(text_no):
    # Mark text as unread in all recipient conferences
    
    raise NotImplementedError()
