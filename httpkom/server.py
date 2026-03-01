# -*- coding: utf-8 -*-
# Copyright (C) 2021 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from quart import g, jsonify

from .komserialization import to_dict

from httpkom import bp
from .sessions import requires_session


@bp.route('/server/info', methods=['GET'])
@requires_session
async def server_info():
    """Get information about the LysKOM server.

    .. rubric:: Request

    ::

      GET /<server_id>/server/info HTTP/1.1

    .. rubric:: Response

    ::

      HTTP/1.1 200 OK

      {
        "version": "2.1.2",
        "conf_pres_conf": 1,
        "pers_pres_conf": 2,
        "motd_conf": 3,
        "kom_news_conf": 4,
        "mot_of_day": 0
      }

    .. rubric:: Example

    ::

      curl -v "http://localhost:5001/lyskom/server/info"

    """
    return jsonify(await to_dict(await g.ksession.get_server_info(), g.ksession))
