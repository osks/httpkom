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


Development
-----------

Preparing a release
*******************

TODO: How do we update the documentation on github pages?

On master:

1. Update and check CHANGELOG.md.

2. Increment version number and remove ``+dev`` suffix
   IN BOTH ``setup.py`` AND ``httpkom/version.py``!

3. Test manually by using jskom.

4. Commit, push.

5. Tag (annotated) with ``v<version>`` (example: ``v0.1``) and push the tag::

       git tag -a v0.1 -m "Version 0.1"
       git push origin v0.1

6. Build PyPI dist: ``make dist``

7. Push to Test PyPI: ``twine upload --repository testpypi dist/*`` and check
   https://test.pypi.org/project/httpkom/ .

8. Push to PyPI: ``twine upload dist/*`` and check
   https://pypi.org/project/httpkom/ .

9. Add ``+dev`` suffix to version number, commit and push.


Tools
*****

Install and update release tools with::

    pip install --upgrade setuptools wheel pip twine

Twine is used for pushing the built dist to PyPI. The examples in the
release process depends on a ``.pypirc`` file with config for the pypi
and testpypi repositories.

Example of ``.pypirc``::

    [pypi]
    username = __token__
    password = pypi-...

    [testpypi]
    repository = https://test.pypi.org/legacy/
    username = __token__
    password = pypi-...


Authors
-------

Oskar Skoog <oskar@osd.se>


Copyright and license
---------------------

Copyright (C) 2012-2021 Oskar Skoog

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
