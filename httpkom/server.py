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
    return jsonify(await to_dict(await g.ksession.get_server_info(), g.ksession))
