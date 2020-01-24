# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import

from io import BytesIO

from flask import g, request, jsonify, send_file, url_for

import pylyskom.errors as komerror
from pylyskom.utils import parse_content_type

from .komserialization import to_dict

from httpkom import bp
from .errors import error_response
from .misc import empty_response
from .sessions import requires_login


@bp.route('/texts/<int:text_no>')
@requires_login
def texts_get(text_no):
    """Get a text.
    
    Note: The body will only be included in the response if the content type is text.
    
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/texts/19680717 HTTP/1.0
    
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
        "creation_time": "2013-11-30T15:58:06Z",
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
    
      curl -v -X GET -H "Content-Type: application/json" \\
           "http://localhost:5001/lyskom/texts/19680717"
    
    """
    try:
        return jsonify(to_dict(g.ksession.get_text(text_no), True, g.ksession))
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/<int:text_no>/body')
@requires_login
def texts_get_body(text_no):
    """Get the body of text, with the content type of the body set in the HTTP header.
    Useful for creating img-tags in HTML and specifying this URL as source.
    
    If the content type is text, the text will be recoded to UTF-8. For other types,
    the content type will be left untouched.
    
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/texts/19680717/body HTTP/1.0
    
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
    
      curl -v -X GET -H "Content-Type: application/json" \\
           "http://localhost:5001/lyskom/texts/19680717/body"
    
    """
    try:
        text = g.ksession.get_text(text_no)
        mime_type, encoding = parse_content_type(text.content_type)
        
        if mime_type[0] == 'text':
            data = BytesIO(text.body.encode('utf-8'))
        else:
            data = BytesIO(text.body)
        response = send_file(data,
                             mimetype=text.content_type,
                             as_attachment=False)
            
        return response
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/', methods=['POST'])
@requires_login
def texts_create():
    """Create a text.

    .. rubric:: Request

    ::

      POST /<server_id>/texts/ HTTP/1.0

      {
        "body": "r\u00e4ksm\u00f6rg\u00e5s",
        "subject": "jaha",
        "recipient_list": [ { "type": "to", "recpt": { "conf_no": 14506 } } ],
        "content_type": "text/x-kom-basic",
        "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ]
      }

    .. rubric:: Responses

    Text was created::

      HTTP/1.0 201 Created
      Location: http://localhost:5001/<server_id>/texts/19724960

      {
        "text_no": 19724960,
      }

    .. rubric:: Example text:

    ::

      curl -v -X POST -H "Content-Type: application/json" \\
           -d '{ "body": "r\u00e4ksm\u00f6rg\u00e5s", \\
                 "subject": "jaha",
                 "recipipent_list": [ { recpt: { "conf_no": 14506 }, "type": "to" } ], \\
                 "content_type": "text/x-kom-basic", \\
                 "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ] }' \\
           "http://localhost:5001/lyskom/texts/"


    .. rubric:: Example image:

    ::

      curl -v -X POST -H "Content-Type: application/json" \\
           -d '{ "body": <base64>, \\
                 "subject": "jaha",
                 "recipipent_list": [ { recpt: { "conf_no": 14506 }, "type": "to" } ], \\
                 "content_type": "image/jpeg", \\
                 "content_encoding": "base64", \\
                 "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ] }' \\
           "http://localhost:5001/lyskom/texts/"

    """
    subject = request.json['subject']
    body = request.json['body']
    content_type = request.json['content_type']
    content_encoding = request.json.get('content_encoding', None)
    recipient_list = request.json.get('recipient_list', None)
    comment_to_list = request.json.get('comment_to_list', None)

    text_no = g.ksession.create_text(subject, body, content_type, content_encoding, recipient_list, comment_to_list)

    headers = { "Location": url_for(".texts_get", server_id=g.server.id, text_no=text_no) }
    return jsonify(text_no=text_no), 201, headers


@bp.route('/texts/marks/')
@requires_login
def texts_get_marks():
    """Get the list of marked texts.
    
    .. rubric:: Request
    
    ::
    
      GET /<server_id>/texts/marks/ HTTP/1.1
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.1 200 OK
      
      {
        "marks": [
          { "text_no": 4711, "type": 100 },
          { "text_no": 4999999, "type": 101 },
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -v -X GET -H "Content-Type: application/json" \\
           "http://localhost:5001/lyskom/texts/marks/"
    
    """
    return jsonify(dict(marks=to_dict(g.ksession.get_marks(), True, g.ksession)))


@bp.route('/texts/<int:text_no>/mark', methods=['PUT'])
@requires_login
def texts_put_mark(text_no):
    """Mark a text.
    
    .. rubric:: Request
    
    ::
    
      PUT /<server_id>/texts/<text_no>/mark HTTP/1.1
      
      {
        "type": 100
      }
    
    .. rubric:: Response
    
    Success::
    
      HTTP/1.1 201 Created
    
    .. rubric:: Example
    
    ::
    
      curl -v -X PUT -H "Content-Type: application/json" \\
           -d { "type": 100 } \\
           "http://localhost:5001/lyskom/texts/4711/mark"
    
    """
    try:
        mark_type = request.json['type']
    except KeyError:
        return error_response(400, error_msg='Missing "type".')
    
    try:
        g.ksession.mark_text(text_no, mark_type)
        return empty_response(201)
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/<int:text_no>/mark', methods=['DELETE'])
@requires_login
def texts_delete_mark(text_no):
    """Unmark a text.
    
    .. rubric:: Request
    
    ::
    
      DELETE /<server_id>/texts/<text_no>/mark HTTP/1.1
    
    .. rubric:: Response
    
    Success::
    
      HTTP/1.1 204 OK
    
    .. rubric:: Example
    
    ::
    
      curl -v -X DELETE "http://localhost:5001/lyskom/texts/4711/mark"
    
    """
    try:
        g.ksession.unmark_text(text_no)
        return empty_response(204)
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/<int:text_no>/read-marking', methods=['PUT'])
@requires_login
def texts_put_read_marking(text_no):
    """Mark a text as read in all recipient conferences.
    
    .. rubric:: Request
    
    ::
    
      PUT /<server_id>/texts/<int:text_no>/read-marking HTTP/1.0
    
    .. rubric:: Responses
    
    Text was marked as read::
    
      HTTP/1.0 201 Created
    
    .. rubric:: Example
    
    ::
    
      curl -v -X PUT "http://localhost:5001/lyskom/texts/19680717/read-marking"
    
    """
    g.ksession.mark_as_read(text_no)
    return empty_response(201)


@bp.route('/texts/<int:text_no>/read-marking', methods=['DELETE'])
@requires_login
def texts_delete_read_marking(text_no):
    """Mark a text as unread in all recipient conferences.
    
    .. rubric:: Request
    
    ::
    
      DELETE /<server_id>/texts/<int:text_no>/read-marking HTTP/1.0
    
    .. rubric:: Responses
    
    Text was marked as read::
    
      HTTP/1.0 204 NO CONTENT
    
    .. rubric:: Example
    
    ::
    
      curl -v DELETE "http://localhost:5001/lyskom/texts/19680717/read-marking"
    
    """
    g.ksession.mark_as_unread(text_no)
    return empty_response(204)
