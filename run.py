#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run test server in development
"""

from rest_api import app

app.run(host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'])
