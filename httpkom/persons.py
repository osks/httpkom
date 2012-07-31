# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from flask import g, request, jsonify, Response

import kom
from komsession import KomSession, KomSessionError, to_dict

from httpkom import app
from errors import error_response
from misc import empty_response
from sessions import optional_session


_kom_server = app.config['HTTPKOM_LYSKOM_SERVER']


@app.route('/persons/')
@optional_session
def persons_list():
    """Lookup person names.
    
    An existing session is not required, but if one exist (i.e. valid
    cookie) it will be used. Otherwise a new session will be created
    temporarily for this request.
    
    Query parameters:
    
    =======  =======  =================================================================
    Key      Type     Values
    =======  =======  =================================================================
    name     string   Name to look up according to `KOM conventions <http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#Name%20Expansion>`_.
    =======  =======  =================================================================
    
    .. rubric:: Request
    
    ::
    
      GET /persons/?name=Osk%20t HTTP/1.0
    
    .. rubric:: Response
    
    ::
    
      HTTP/1.0 200 OK
      
      {
        "persons": [
          {
            "pers_no": 13212, 
            "pers_name": "Oskars tredje person"
          }, 
          {
            "pers_no": 14506, 
            "pers_name": "Oskars Testperson"
          }
        ]
      }
    
    .. rubric:: Example
    
    ::
    
      curl -b cookies.txt -c cookies.txt -v \\
           -X GET -H "Content-Type: application/json" \\
           http://localhost:5001/persons/?name=Osk%20t
    
    """
    
    name = request.args['name']
    if g.ksession:
        # Use exising session if we have one
        ksession = g.ksession
    else:
        # .. otherwise create a new temporary session
        ksession = KomSession(_kom_server)
        ksession.connect()
        
    try:
        lookup = ksession.lookup_name(name, True, False)
        persons = [ dict(pers_no=t[0], pers_name=t[1]) for t in lookup ]
        return jsonify(dict(persons=persons))
    except kom.Error as ex:
        return error_response(400, kom_error=ex)
    finally:
        # if we created a new session, close it
        if not g.ksession:
            ksession.disconnect()
