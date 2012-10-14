httpkom
=======

httpkom is an HTTP proxy for LysKOM protocol A servers, and exposes an
REST-like HTTP API. It can for example be used for writing LysKOM
clients in Javascript.

The source code can be found at: https://github.com/osks/httpkom

httpkom uses python-lyskom, which is also released under GPL. The
following files belong to python-lyskom: httpkom/kom.py,
httpkom/thkom.py and httpkom/komauxitems.py.

The debug server in httpkom uses gevent, which in its turn uses
libevent. If you use Homebrew on OS X you can install libevent and
gevent like this, assuming Homebrew is located in /opt/homebrew:

$ brew install libevent

$ CFLAGS="-I /opt/homebrew/include -L /opt/homebrew/lib" \
  pip install gevent

Right now httpkom doesn't depend on gevent other than that, but it
probably will in the future.


Dependencies
------------

For required Python packages, see requirements.txt. Install them with:

  $ pip install -r requirements.txt


Authors
-------

Oskar Skoog <oskar@osd.se>


Copyright and license
---------------------

Copyright (C) 2012 Oskar Skoog

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
