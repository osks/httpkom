# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import

import asyncio
from io import BytesIO

from quart import g, request, jsonify, send_file, url_for

import pylyskom.errors as komerror
from pylyskom.utils import parse_content_type

from .komserialization import to_dict, KomTextStat_to_dict

from httpkom import bp
from .errors import error_response
from .misc import empty_response
from .sessions import requires_login


@bp.route('/texts/<int:text_no>')
@requires_login
async def texts_get(text_no):
    """Get a text.

    Note: The body will only be included in the response if the content type is text.

    **Request:**

    ```
    GET /<server_id>/texts/19680717 HTTP/1.0
    ```

    **Responses:**

    Text exists:

    ```json
    HTTP/1.0 200 OK

    {
      "body": "r\u00e4ksm\u00f6rg\u00e5s",
      "recipient_list": [
        {
          "recpt": {
            "conf_no": 14506
            "name": "Oskars Testperson",
          },
          "type": "to",
          "loc_no": 29,
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
    ```

    Text does not exist:

    ```
    HTTP/1.0 404 NOT FOUND

    { TODO: error stuff }
    ```

    **Example:**

    ```bash
    curl -v -X GET -H "Content-Type: application/json" \\
         "http://localhost:5001/lyskom/texts/19680717"
    ```

    """
    try:
        return jsonify(await to_dict(await g.ksession.get_text(text_no), g.ksession))
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/textstats/<int:text_no>')
@requires_login
async def textstats_get(text_no):
    """Get text stat (metadata without body/subject).

    Same shape as GET /texts/<text_no> but without subject, body, and
    content_type. Useful for comment-tree discovery without fetching
    full text bodies.

    **Request:**

    ```
    GET /<server_id>/textstats/19680717 HTTP/1.1
    ```

    """
    try:
        return jsonify(await KomTextStat_to_dict(
            await g.ksession.get_text_stat(text_no), g.ksession))
    except (komerror.NoSuchText, komerror.TextZero) as ex:
        return error_response(404, kom_error=ex)


@bp.route('/textstats', methods=['POST'])
@requires_login
async def textstats_batch():
    """Get text stats for multiple texts in one request.

    **Request:**

    ```
    POST /<server_id>/textstats HTTP/1.1

    {
      "text_nos": [100, 101, 102]
    }
    ```

    **Response:**

    ```json
    HTTP/1.1 200 OK

    {
      "text_stats": {
        "100": { ... },
        "101": { ... },
        "102": null
      }
    }
    ```

    Missing texts are returned as null. Maximum 100 text numbers per request.

    """
    request_json = await request.json
    text_nos = request_json.get('text_nos', [])
    if len(text_nos) > 100:
        return error_response(400, error_msg='Maximum 100 text numbers per request.')

    async def get_one(text_no):
        try:
            ts = await g.ksession.get_text_stat(text_no)
            return str(text_no), await KomTextStat_to_dict(ts, g.ksession)
        except (komerror.NoSuchText, komerror.TextZero):
            return str(text_no), None

    results = await asyncio.gather(*[get_one(no) for no in text_nos])
    return jsonify(text_stats=dict(results))


@bp.route('/texts/<int:text_no>/body')
@requires_login
async def texts_get_body(text_no):
    """Get the body of text, with the content type of the body set in the HTTP header.
    Useful for creating img-tags in HTML and specifying this URL as source.

    If the content type is text, the text will be recoded to UTF-8. For other types,
    the content type will be left untouched.

    **Request:**

    ```
    GET /<server_id>/texts/19680717/body HTTP/1.0
    ```

    **Responses:**

    Text exists:

    ```
    HTTP/1.0 200 OK
    Content-Type: text/x-kom-basic; charset=utf-8

    räksmörgås
    ```

    Text does not exist:

    ```
    HTTP/1.0 404 NOT FOUND

    { TODO: error stuff }
    ```

    **Example:**

    ```bash
    curl -v -X GET -H "Content-Type: application/json" \\
         "http://localhost:5001/lyskom/texts/19680717/body"
    ```

    """
    try:
        text = await g.ksession.get_text(text_no)
        mime_type, encoding = parse_content_type(text.content_type)
        
        if mime_type[0] == 'text':
            data = BytesIO(text.body.encode('utf-8'))
        else:
            data = BytesIO(text.body)
        response = await send_file(data,
                                   mimetype=text.content_type,
                                   as_attachment=False)
            
        return response
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/', methods=['POST'])
@requires_login
async def texts_create():
    """Create a text.

    **Request:**

    ```
    POST /<server_id>/texts/ HTTP/1.0

    {
      "body": "r\u00e4ksm\u00f6rg\u00e5s",
      "subject": "jaha",
      "recipient_list": [ { "type": "to", "recpt": { "conf_no": 14506 } } ],
      "content_type": "text/x-kom-basic",
      "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ]
    }
    ```

    **Responses:**

    Text was created:

    ```json
    HTTP/1.0 201 Created
    Location: http://localhost:5001/<server_id>/texts/19724960

    {
      "text_no": 19724960,
    }
    ```

    **Example text:**

    ```bash
    curl -v -X POST -H "Content-Type: application/json" \\
         -d '{ "body": "r\u00e4ksm\u00f6rg\u00e5s", \\
               "subject": "jaha", \\
               "recipient_list": [ { "recpt": { "conf_no": 14506 }, "type": "to" } ], \\
               "content_type": "text/x-kom-basic", \\
               "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ] }' \\
         "http://localhost:5001/lyskom/texts/"
    ```

    **Example image:**

    ```bash
    curl -v -X POST -H "Content-Type: application/json" \\
         -d '{ "body": "<base64>", \\
               "subject": "jaha", \\
               "recipient_list": [ { "recpt": { "conf_no": 14506 }, "type": "to" } ], \\
               "content_type": "image/jpeg", \\
               "content_encoding": "base64", \\
               "comment_to_list": [ { "type": "footnote", "text_no": 19675793 } ] }' \\
         "http://localhost:5001/lyskom/texts/"
    ```

    """
    request_json = await request.json
    subject = request_json['subject']
    body = request_json['body']
    content_type = request_json['content_type']
    content_encoding = request_json.get('content_encoding', None)
    recipient_list = request_json.get('recipient_list', None)
    comment_to_list = request_json.get('comment_to_list', None)

    text_no = await g.ksession.create_text(subject, body, content_type, content_encoding, recipient_list, comment_to_list)

    headers = { "Location": url_for(".texts_get", server_id=g.server.id, text_no=text_no) }
    return jsonify(text_no=text_no), 201, headers


@bp.route('/texts/marks/')
@requires_login
async def texts_get_marks():
    """Get the list of marked texts.

    **Request:**

    ```
    GET /<server_id>/texts/marks/ HTTP/1.1
    ```

    **Response:**

    ```json
    HTTP/1.1 200 OK

    {
      "marks": [
        { "text_no": 4711, "type": 100 },
        { "text_no": 4999999, "type": 101 },
      ]
    }
    ```

    **Example:**

    ```bash
    curl -v -X GET -H "Content-Type: application/json" \\
         "http://localhost:5001/lyskom/texts/marks/"
    ```

    """
    return jsonify(dict(marks=await to_dict(await g.ksession.get_marks(), g.ksession)))


@bp.route('/texts/<int:text_no>/mark', methods=['PUT'])
@requires_login
async def texts_put_mark(text_no):
    """Mark a text.

    **Request:**

    ```
    PUT /<server_id>/texts/<text_no>/mark HTTP/1.1

    {
      "type": 100
    }
    ```

    **Response:**

    Success:

    ```
    HTTP/1.1 201 Created
    ```

    **Example:**

    ```bash
    curl -v -X PUT -H "Content-Type: application/json" \\
         -d { "type": 100 } \\
         "http://localhost:5001/lyskom/texts/4711/mark"
    ```

    """
    request_json = await request.json
    try:
        mark_type = request_json['type']
    except KeyError:
        return error_response(400, error_msg='Missing "type".')
    
    try:
        await g.ksession.mark_text(text_no, mark_type)
        return empty_response(201)
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/<int:text_no>/mark', methods=['DELETE'])
@requires_login
async def texts_delete_mark(text_no):
    """Unmark a text.

    **Request:**

    ```
    DELETE /<server_id>/texts/<text_no>/mark HTTP/1.1
    ```

    **Response:**

    Success:

    ```
    HTTP/1.1 204 OK
    ```

    **Example:**

    ```bash
    curl -v -X DELETE "http://localhost:5001/lyskom/texts/4711/mark"
    ```

    """
    try:
        await g.ksession.unmark_text(text_no)
        return empty_response(204)
    except komerror.NoSuchText as ex:
        return error_response(404, kom_error=ex)


@bp.route('/texts/<int:text_no>/read-marking', methods=['PUT'])
@requires_login
async def texts_put_read_marking(text_no):
    """Mark a text as read in all recipient conferences.

    **Request:**

    ```
    PUT /<server_id>/texts/<int:text_no>/read-marking HTTP/1.0
    ```

    **Responses:**

    Text was marked as read:

    ```
    HTTP/1.0 201 Created
    ```

    **Example:**

    ```bash
    curl -v -X PUT "http://localhost:5001/lyskom/texts/19680717/read-marking"
    ```

    """
    await g.ksession.mark_as_read(text_no)
    return empty_response(201)


@bp.route('/texts/<int:text_no>/read-marking', methods=['DELETE'])
@requires_login
async def texts_delete_read_marking(text_no):
    """Mark a text as unread in all recipient conferences.

    **Request:**

    ```
    DELETE /<server_id>/texts/<int:text_no>/read-marking HTTP/1.0
    ```

    **Responses:**

    Text was marked as unread:

    ```
    HTTP/1.0 204 NO CONTENT
    ```

    **Example:**

    ```bash
    curl -v -X DELETE "http://localhost:5001/lyskom/texts/19680717/read-marking"
    ```

    """
    await g.ksession.mark_as_unread(text_no)
    return empty_response(204)
