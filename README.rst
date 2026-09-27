httpkom
=======

httpkom is an HTTP proxy for LysKOM protocol A servers, and exposes an
REST-like HTTP API. It can for example be used for writing LysKOM
clients in Javascript.

The source code can be found at: https://github.com/osks/httpkom

Packages are published on PyPI: https://pypi.org/project/httpkom/

The documentation can be found at: http://osks.github.io/httpkom/

httpkom uses `pylyskom <https://github.com/osks/pylyskom>`_, which
is also released under GPL.


Dependencies
------------

For required Python packages, see requirements.txt. Install them with::

    $ pip install -r requirements.txt


Documentation
-------------

The documentation is built with `MkDocs <https://www.mkdocs.org/>`_ and
`Material for MkDocs <https://squidfunk.github.io/mkdocs-material/>`_.
Source files are in the ``docs/`` directory.

To serve the docs locally::

    uv run mkdocs serve

The docs are automatically deployed to GitHub Pages on push to master
via GitHub Actions (see ``.github/workflows/docs.yml``).


Running
-------

::

    python -m httpkom --config httpkom.cfg --host 127.0.0.1 --port 5001

Options:

``--config`` (required)
    Config file. ``HTTPKOM_LYSKOM_SERVERS`` lists the LysKOM servers
    clients can connect to, e.g.
    ``[('lyskom', 'LysKOM', 'kom.lysator.liu.se', 4894)]``.

``--host``, ``--port``
    Where to listen (default ``0.0.0.0:5001``).

``--log-level``
    ``DEBUG``, ``INFO`` (default), ``WARNING`` or ``ERROR``. ``DEBUG``
    logs all LysKOM protocol traffic, including the contents of texts,
    so don't use it in production.

``--graphite-host``, ``--graphite-port``
    Send stats to Graphite (off unless a host is given).

Logging
*******

At ``INFO``, session events are logged, each tagged with the first 8
hex characters of the SHA-256 of the connection id. The tag lets you
follow one session through the log without logging the connection id
itself, which works like a password::

    [2b01858d] session created: server lyskom, session 3109680, client jskom 2.0 (4 active)
    [2b01858d] login: person 10647
    [2b01858d] login failed: InvalidPassword
    [2b01858d] logout
    [2b01858d] session removed: disconnected (3 active)
    [2b01858d] session removed: connection to LysKOM lost (3 active)
    [ef2e7fb3] unknown session, returning 403

Errors are logged with stack traces. Requests themselves are not
logged; put a proxy with an access log in front of httpkom for that.


Development
-----------

Preparing a release
*******************

On master:

1. Update and check CHANGELOG.md.

2. Increment version number and remove ``+dev`` suffix
   in ``httpkom/version.py``.

3. Test manually by using jskom.

4. Commit, push.

5. Go to https://github.com/osks/httpkom/releases and draft a new
   release. Create a new tag (e.g. ``v0.21``), set title to
   "Version <version>", and publish the release.

6. GitHub Actions will automatically build and publish to PyPI
   (see ``.github/workflows/release.yml``).

7. Verify at https://pypi.org/project/httpkom/ .

8. Add ``+dev`` suffix to version number, commit and push.


Authors
-------

Oskar Skoog <oskar@osd.se>


Copyright and license
---------------------

Copyright (C) 2012-2026 Oskar Skoog

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA  02110-1301, USA.
