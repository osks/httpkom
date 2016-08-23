# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from flask import jsonify

from pylyskom.errors import error_dict, ServerError, LoginFirst, LocalError
from pylyskom.komsession import KomSessionError

from httpkom import app
from .misc import empty_response
from .stats import stats


# Only kom.ServerErrors in this dict (i.e. errors defined by Protocol A).
_kom_servererror_code_dict = dict([v,k] for k,v in error_dict.items())


def _kom_servererror_to_error_code(ex):
    if ex.__class__ in _kom_servererror_code_dict:
        return _kom_servererror_code_dict[ex.__class__]
    else:
        return None

def error_response(status_code, kom_error=None, error_msg=""):
    # TODO: I think we need to unify these error types to make the API
    # easier. Perhaps use protocol a error codes as they are, and
    # add our own httpkom error codes on 1000 and above?
    if kom_error is not None:
        # The error should exist in the dictionary, but we use .get() to be safe
        response = jsonify(error_code=_kom_servererror_to_error_code(kom_error),
                           error_status=str(kom_error),
                           error_type="protocol-a",
                           error_msg=str(kom_error.__class__.__name__))
    else:
        # We don't have any fancy error codes for httpkom yet.
        response = jsonify(error_type="httpkom",
                           error_msg=error_msg)
    
    response.status_code = status_code
    return response


@app.errorhandler(400)
def badrequest(error):
    app.logger.exception(error)
    stats.set('http.errors.badrequest.last', 1, agg='sum')
    return empty_response(400)

@app.errorhandler(404)
def notfound(error):
    stats.set('http.errors.notfound.last', 1, agg='sum')
    return empty_response(404)

@app.errorhandler(ServerError)
def kom_server_error(error):
    app.logger.exception(error)
    status = 400
    if isinstance(error, LoginFirst):
        status = 401
    stats.set('http.errors.komservererror.last', 1, agg='sum')
    return error_response(status, kom_error=error)

@app.errorhandler(LocalError)
def kom_local_error(error):
    app.logger.exception(error)
    stats.set('http.errors.komlocalerror.last', 1, agg='sum')
    return error_response(500, error_msg=str(error))

@app.errorhandler(KomSessionError)
def komsession_error(error):
    app.logger.exception(error)
    stats.set('http.errors.komsessionerror.last', 1, agg='sum')
    return error_response(400, error_msg=str(error))

@app.errorhandler(500)
def internalservererror(error):
    app.logger.exception(error)
    stats.set('http.errors.internalservererror.last', 1, agg='sum')
    return error_response(500, error_msg=str(error))

@app.errorhandler(Exception)
def exceptionhandler(error):
    app.logger.exception(error)
    stats.set('http.errors.exception.last', 1, agg='sum')
    return error_response(500, error_msg="Unknown error")
