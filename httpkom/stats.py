from flask import jsonify
from pylyskom.stats import Stats
from pylyskom.stats import stats as pylyskom_stats

from httpkom import app


stats = Stats(prefix='httpkom.')


@app.route("/stats")
def get_stats():
    s = _merge_two_dicts(stats.dump(), pylyskom_stats.dump())
    return jsonify(s)


@app.before_request
def stats_request_count():
    try:
        stats.set('http.requests.received.last', 1, agg='sum')
    except Exception:
        app.logger.exception("Failed to record received request count")


@app.after_request
def stats_response_status(response):
    try:
        stats.set('http.responses.sent.{}.last'.format(response.status_code), 1, agg='sum')
    except Exception:
        app.logger.exception("Failed to record returned request count")
    return response


# http://stackoverflow.com/questions/38987/how-can-i-merge-two-python-dictionaries-in-a-single-expression
def _merge_two_dicts(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z
