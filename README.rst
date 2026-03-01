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

Copyright (C) 2012-2022 Oskar Skoog

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
