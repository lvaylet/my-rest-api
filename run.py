#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rest_api.app import app

if __name__ == '__main__':
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])
