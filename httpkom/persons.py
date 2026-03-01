# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from quart import g, request, jsonify

import pylyskom.errors as komerror

from .komserialization import to_dict

from httpkom import bp
from .errors import error_response
from .sessions import requires_session, requires_login
from .misc import empty_response


@bp.route('/persons/<int:pers_no>/user-area/<string:block_name>', methods=['GET'])
@requires_login
async def persons_get_user_area_block(pers_no, block_name):
    """Get a user area block.

    Args:
        pers_no (int): Person number.
        block_name (string): Name of the user area block.

    **Request:**

    ```
    GET /<server_id>/persons/<pers_no>/user-area/<block_name> HTTP/1.1
    ```

    **Responses:**

    Block exists:

    ```json
    HTTP/1.1 200 OK

    { ... }
    ```

    Block does not exist:

    ```
    HTTP/1.1 404 NOT FOUND
    ```

    **Example:**

    ```bash
    curl -v "http://localhost:5001/lyskom/persons/14506/user-area/common"
    ```

    """
    block = await g.ksession.get_user_area_block(pers_no, block_name)
    if block is None:
        return empty_response(404)
    return jsonify(block)


@bp.route('/persons/<int:pers_no>/set-presentation', methods=['POST'])
@requires_login
async def persons_set_presentation(pers_no):
    """Set the presentation text for a person.

    Args:
        pers_no (int): Person number.

    **Request:**

    ```
    POST /<server_id>/persons/<pers_no>/set-presentation HTTP/1.1

    {
      "text_no": 19680717
    }
    ```

    **Response:**

    Success:

    ```
    HTTP/1.1 201 Created
    ```

    **Example:**

    ```bash
    curl -v -X POST -H "Content-Type: application/json" \\
         -d '{ "text_no": 19680717 }' \\
         "http://localhost:5001/lyskom/persons/14506/set-presentation"
    ```

    """
    request_json = await request.json
    text_no = request_json['text_no']
    try:
        await g.ksession.set_presentation(pers_no, text_no)
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)
    return empty_response(201)


@bp.route('/persons/<int:pers_no>/set-passwd', methods=['POST'])
@requires_login
async def persons_set_passwd(pers_no):
    """Change password for a person.

    Args:
        pers_no (int): Person number.

    **Request:**

    ```
    POST /<server_id>/persons/<pers_no>/set-passwd HTTP/1.1

    {
      "old_pwd": "oldpassword",
      "new_pwd": "newpassword"
    }
    ```

    **Response:**

    Success:

    ```
    HTTP/1.1 201 Created
    ```

    **Example:**

    ```bash
    curl -v -X POST -H "Content-Type: application/json" \\
         -d '{ "old_pwd": "oldpassword", "new_pwd": "newpassword" }' \\
         "http://localhost:5001/lyskom/persons/14506/set-passwd"
    ```

    """
    request_json = await request.json
    old_pwd = request_json['old_pwd']
    new_pwd = request_json['new_pwd']
    try:
        await g.ksession.set_passwd(pers_no, old_pwd, new_pwd)
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)
    return empty_response(201)


@bp.route('/persons/', methods=['POST'])
@requires_session
async def persons_create():
    """Create a person.

    **Request:**

    ```
    POST /<server_id>/persons/ HTTP/1.0

    {
      "name": "Oskars Testperson",
      "passwd": "test123",
    }
    ```

    **Responses:**

    Person was created:

    ```json
    HTTP/1.0 201 Created

    {
      "pers_no": 14506,
      "pers_name": "Oskars Testperson"
    }
    ```

    **Example:**

    ```bash
    curl -v -X POST -H "Content-Type: application/json" \\
         -d '{ "name": "Oskar Testperson", "passwd": "test123" }' \\
         http://localhost:5001/lyskom/persons/
    ```

    """
    request_json = await request.json
    name = request_json['name']
    passwd = request_json['passwd']
    
    try:
        kom_person = await g.ksession.create_person(name, passwd)
        return jsonify(await to_dict(kom_person, g.ksession)), 201
    except komerror.Error as ex:
        return error_response(400, kom_error=ex)
